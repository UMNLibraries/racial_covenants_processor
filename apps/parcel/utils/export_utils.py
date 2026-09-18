import datetime
import json

import geopandas as gpd
import numpy as np
import pandas as pd
from django.contrib.gis.db.models.functions import AsGeoJSON, AsWKT, Centroid
from django.db.models import F

from apps.deed.models import DeedPage
from apps.parcel.models import CovenantedParcel, Parcel
from apps.zoon.models import (
    MANUAL_COV_OPTIONS,
    MATCH_TYPE_OPTIONS,
    ManualCovenant,
    ZooniverseSubject,
)
from apps.zoon.utils.zooniverse_load import get_full_url, get_image_url_prefix

MATCH_TYPES = MATCH_TYPE_OPTIONS + MANUAL_COV_OPTIONS

EXPORT_FIELDS_ORDERED = [
    "db_id",
    "workflow",
    "cnty_name",
    "cnty_fips",
    "doc_num",
    "main_image",
    "deed_year",
    "deed_date",
    # 'exec_date',
    "cov_text",
    "seller",
    "buyer",
    "street_add",
    "city",
    "state",
    "zip_code",
    "add_cov",
    "block_cov",
    "lot_cov",
    "map_book",
    "map_page",
    "cnty_pin",
    "add_mod",
    "block_mod",
    "lot_mod",
    "ph_dsc_mod",
    "join_strgs",
    "geocd_addr",
    "geocd_dist",
    "cov_type",
    "match_type",
    "manual_cx",
    "dt_updated",
    "zn_subj_id",
    "zn_dt_ret",
    "image_ids",
    "med_score",
    "plat_dbid",
    "subd_dbid",
]


def delete_flat_covenanted_parcels(parcels):
    existing_covs = CovenantedParcel.objects.filter(
        parcel__pk__in=parcels.values_list("pk", flat=True)
    )
    if existing_covs.count() > 0:
        print(f"Deleting existing covs: {existing_covs}")

        existing_covs.delete()

    return parcels


def year_or_null(date_obj):
    try:
        return date_obj.year
    except:
        return None


def join_strings_to_str(join_candidates):
    # There may not be join candidates in some cases, e.g. addition-wide covenants
    try:
        return ";".join([jc["join_string"] for jc in join_candidates])
    except TypeError:
        return ""


def match_type_to_str(match_type):
    try:
        return (
            [mt[1] for mt in MATCH_TYPES if mt[0] == match_type][0]
            if match_type is not None
            else "Automatic match"
        )
    except IndexError:
        return "Something else"


def save_flat_covenanted_parcels(parcels):
    """Take a queryset of covenanted parcels instances and make flat CovenantedParcel export instance using Parcel.covenanted_parcels model manager."""

    PARCEL_MODEL_FIELDS = [
        "id",
        "cnty_name",
        "cnty_fips",
        "doc_num",
        "main_image",
        "cnty_pin",
        "deed_date",
        "seller",
        "buyer",
        "cov_type",
        "cov_text",
        "zn_subj_id",
        "zn_dt_ret",
        "deed_page_1",
        "deed_page_2",
        "deed_page_3",
        "med_score",
        "manual_cx",
        "match_type",
        "join_candidates",
        "street_add",
        "city",
        "state",
        "zip_code",
        "add_cov",
        "block_cov",
        "lot_cov",
        "map_book",
        "map_page",
        "add_mod",
        "block_mod",
        "lot_mod",
        "ph_dsc_mod",
        "plat__pk",
        "subdivision_spatial__pk",
        "dt_updated",
        "geom_4326",
    ]

    parcel_pks = parcels.values_list("pk", flat=True)

    if len(parcel_pks) == 0:
        print("No mapped covenants to export.")
        return False
    else:
        cov_creation_objs = []

        parcel_covenants = Parcel.covenant_objects.filter(pk__in=parcel_pks).values(
            *PARCEL_MODEL_FIELDS
        )
        covenants_df = pd.DataFrame(parcel_covenants)
        covenants_df["workflow"] = parcels.first().workflow

        covenants_df["deed_date"] = covenants_df["deed_date"].apply(
            lambda x: pd.to_datetime(x, errors="coerce", format="%Y-%m-%d")
        )
        covenants_df["deed_year"] = covenants_df["deed_date"].apply(
            lambda x: year_or_null(x)
        )
        covenants_df["deed_year"] = (
            covenants_df["deed_year"].fillna(np.nan).replace([np.nan], [None])
        )

        covenants_df["dt_updated"] = pd.DatetimeIndex(covenants_df["dt_updated"]).date

        covenants_df["join_strgs"] = covenants_df["join_candidates"].apply(
            lambda x: join_strings_to_str(x)
        )
        covenants_df["match_type"] = covenants_df["match_type"].apply(
            lambda x: match_type_to_str(x)
        )
        covenants_df["image_ids"] = covenants_df[
            ["deed_page_1", "deed_page_2", "deed_page_3"]
        ].apply(lambda x: ",".join(x.dropna()), axis=1)

        covenants_df.rename(
            columns={
                "id": "parcel_id",  # Set foreign key to parcel
                "plat__pk": "plat_dbid",  # These can just be text representations
                "subdivision_spatial__pk": "subd_dbid",  # These can just be text representations
            },
            inplace=True,
        )

        # Delete unnecessary fields
        covenants_df.drop(
            columns=["join_candidates", "deed_page_1", "deed_page_2", "deed_page_3"],
            inplace=True,
        )

        # Fill nulls
        covenants_df = covenants_df.fillna(np.nan).replace([np.nan], [None])

        for p in covenants_df.to_dict("records"):
            cp = CovenantedParcel(**p)
            cov_creation_objs.append(cp)

        print(f"Creating {len(cov_creation_objs)} CovenantedParcel objects...")

        CovenantedParcel.objects.bulk_create(cov_creation_objs)

        workflow = parcels.first().workflow
        if workflow is not None:
            from apps.parcel.utils.pmtiles_utils import trigger_pmtiles_export

            trigger_pmtiles_export(workflow)

        return CovenantedParcel.objects.filter(parcel__pk__in=parcel_pks)


def build_gdf(workflow, exclude_child_workflows=False):
    # TODO: Child workflow exports
    child_workflows = workflow.child_export_workflows.all()
    if child_workflows.count() > 0:
        workflows = [workflow] + list(child_workflows)
    else:
        workflows = [workflow]

    joined_covenants = (
        CovenantedParcel.objects.filter(workflow__in=workflows)
        .annotate(wkt_4326=AsWKT("geom_4326"), workflow_slug=F("workflow__slug"))
        .values()
    )

    covenants_df = pd.DataFrame(joined_covenants)

    # TEMP TEMP TEMP until bug #90 closed
    # covenants_df = covenants_df[covenants_df['match_type'] != '']

    # Currently blank fields in existing workflows
    covenants_df[
        [
            # 'doc_num',
            # 'exec_date',
            "geocd_addr",
            "geocd_dist",
        ]
    ] = ""

    # Convert datetime fields to true date
    date_fields = ["deed_date"]
    # print(covenants_df[date_fields])
    covenants_df[date_fields] = covenants_df[date_fields].apply(
        lambda x: pd.to_datetime(x, errors="coerce", format="%Y-%m-%d")
    )

    covenants_df.rename(
        columns={"id": "db_id", "workflow_slug": "workflow", "wkt_4326": "geometry"},
        inplace=True,
    )

    covenants_df = covenants_df[EXPORT_FIELDS_ORDERED + ["geometry"]]

    covenants_df["geometry"] = gpd.GeoSeries.from_wkt(
        covenants_df["geometry"], crs="EPSG:4326"
    )

    covenants_geo_df = gpd.GeoDataFrame(covenants_df, geometry="geometry")

    return covenants_geo_df


def build_unmapped_df(workflow, cnty_name=None, cnty_fips=None):
    # TODO: Child workflow exports
    child_workflows = workflow.child_export_workflows.all()
    if child_workflows.count() > 0:
        workflows = [workflow] + list(child_workflows)
    else:
        workflows = [workflow]

    unmapped_covenants = ZooniverseSubject.unmapped_objects.filter(
        workflow__in=workflows
    ).values(
        "id",
        "workflow__slug",
        "doc_num",
        "deed_date_final",
        "seller_final",
        "buyer_final",
        "cov_type",
        "cov_text",
        "zn_subj_id",
        "zn_dt_ret",
        "image_ids",
        # 'deed_page_1',
        # 'deed_page_2',
        # 'deed_page_3',
        "med_score",
        "manual_cx",
        "match_type",
        "join_candidates",
        "add_cov",
        "block_cov",
        "lot_cov",
        "map_book_final",
        "map_book_page_final",
        "city_cov",
        "dt_updated",
    )

    unmapped_df = pd.DataFrame(unmapped_covenants)
    unmapped_df.rename(
        columns={
            "deed_date_final": "deed_date",
            "workflow__slug": "workflow",
            "seller_final": "seller",
            "buyer_final": "buyer",
            "map_book_final": "map_book",
            "map_book_page_final": "map_page",
        },
        inplace=True,
    )

    # covenants_df['image_ids'] = covenants_df[[
    #     'deed_page_1', 'deed_page_2', 'deed_page_3'
    # ]].apply(lambda x: ','.join(x.dropna()), axis=1)

    unmapped_df["cnty_name"] = cnty_name
    unmapped_df["cnty_fips"] = cnty_fips
    # unmapped_df['match_type'] = 'unmapped'

    return unmapped_df


def build_validation_df(workflow):
    """In contrast to mapped covenants, this is all about Zooniverse stuff, so
    build a DF off the ZooniverseSubject
    as opposed to Parcel.covenant_objects"""

    VALIDATION_ATTRS = [
        "id",
        "workflow",
        "doc_num",
        "deed_date_final",
        # 'seller_final',
        # 'buyer_final',
        "cov_type",
        "cov_text",
        "zn_subj_id",
        "zn_dt_ret",
        "resp_count",
        "med_score",
        "cov_score",
        "hand_score",
        "mtype_score",
        "text_score",
        "add_score",
        "lot_score",
        "block_score",
        "city_score",
        "sell_score",
        "buy_score",
        "manual_cx",
        "match_type",
        "join_candidates",
        "add_cov",
        "block_cov",
        "lot_cov",
        "map_book",
        "map_page",
        "city_cov",
        "dt_updated",
    ]

    validation_subjects = ZooniverseSubject.validation_objects.filter(
        workflow=workflow
    ).values(*VALIDATION_ATTRS)

    # Convert to pandas DF and enforce field order
    validation_df = pd.DataFrame(validation_subjects)[VALIDATION_ATTRS]

    return validation_df


def deduped_str_list(series):
    uniques = set(s for s in series if s)
    if len(uniques) > 0:
        return "; ".join(uniques)
    return ""


def build_all_covenanted_docs_df(workflow):
    """Export all copies of covenanted documents from both ZooniverseSubject and ManualCovenant"""

    ALL_DOCS_ATTRIBUTES = [
        "workflow",
        "cov_type",
        "db_id",
        "doc_num",
        "deed_year",
        "deed_date",
        "cov_text",
        "seller",
        "buyer",
        "add_cov",
        "block_cov",
        "lot_cov",
        "map_book",
        "map_page",
        "is_mapped",
        "addresses",
        "cities",
        "state",
        "cnty_pins",
        "join_strgs",
        "match_type",
        "manual_cx",
        "dt_updated",
        "zn_subj_id",
        "zn_dt_ret",
        "main_image",
        "web_image",
        "highlight_image",
        "image_ids",
        "med_score",
    ]

    # image_links_df = pd.DataFrame(DeedPage.objects.filter(
    #     workflow=workflow,
    #     bool_match=True
    # ).values(
    #     's3_lookup',
    #     'page_image_web',
    #     'page_image_web_highlighted'
    # )).rename(columns={
    #     'page_image_web': 'web_image',
    #     'page_image_web_highlighted': 'highlight_image',
    # })

    # print(image_links_df.shape[0])

    zoon_covenanted_subjects = ZooniverseSubject.all_covenanted_docs_objects.filter(
        workflow=workflow
    ).values(
        "db_id",
        "workflow",
        "is_mapped",
        "deed_date_final",  # Need to rename with pd
        "cov_text",
        "image_ids",
        "zn_subj_id",
        "zn_dt_ret",
        "main_image",
        "web_image",
        "highlight_image",
        "med_score",
        "manual_cx",
        "add_cov",
        "block_cov",
        "lot_cov",
        "map_book_final",  # Need to rename with pd
        "map_book_page_final",  # Need to rename with pd
        "join_strgs",
        "mapped_address",
        "mapped_city",
        "mapped_state",
        "mapped_parcel_pin",
        "seller_final",  # Need to rename with pd
        "buyer_final",  # Need to rename with pd
        "dt_updated",
        "doc_num",
        "cov_type",
        "match_type_final",  # Need to rename with pd =Value('unmapped')
    )

    # print(zoon_covenanted_subjects)

    # return False

    # TK
    all_manual_covenants = ManualCovenant.all_covenanted_docs_objects.filter(
        workflow=workflow
    ).values(
        "db_id",
        "workflow",
        "is_mapped",
        "deed_date",
        "cov_text",
        # 'image_ids',  # Need to set to null with pd
        "zn_subj_id",
        "zn_dt_ret",
        "med_score",
        "manual_cx",
        "add_cov",
        "block_cov",
        "lot_cov",
        "map_book",
        "map_book_page",
        "join_strgs",
        "mapped_address",
        "mapped_city",
        "mapped_state",
        "mapped_parcel_pin",
        "seller",
        "buyer",
        "dt_updated",
        "doc_num",
        "cov_type",  # Need to rename with pd to match_type
        # 'cov_type_manual', # Need to rename with pd to cov_type (janky!)
        # 'match_type',  # Need to rename with pd =Value('unmapped')
    )

    # TODO: fix image ids

    # Convert to pandas DF
    zoon_covenanted_docs_expanded_df = pd.DataFrame(zoon_covenanted_subjects)
    zoon_covenanted_docs_expanded_df.rename(
        columns={
            "deed_date_final": "deed_date",
            "map_book_final": "map_book",
            "map_book_page_final": "map_page",
            "seller_final": "seller",
            "buyer_final": "buyer",
            "city_final": "city",
            "match_type_final": "match_type",
        },
        inplace=True,
    )
    # zoon_covenanted_docs_expanded_df = zoon_covenanted_docs_expanded_df.merge(
    #     image_links_df,
    #     how="left",
    #     left_on="main_image",
    #     right_on="s3_lookup"
    # )

    manual_covenanted_docs_expanded_df = pd.DataFrame(all_manual_covenants)

    manual_covenanted_docs_expanded_df.rename(
        columns={
            "cov_type": "match_type",
            "map_book_page": "map_page",
        },
        inplace=True,
    )
    manual_covenanted_docs_expanded_df["image_ids"] = ""
    manual_covenanted_docs_expanded_df["main_image"] = ""
    manual_covenanted_docs_expanded_df["web_image"] = ""
    manual_covenanted_docs_expanded_df["highlight_image"] = ""
    manual_covenanted_docs_expanded_df["cov_type"] = "manual"

    all_covenanted_docs_expanded_df = pd.concat(
        [zoon_covenanted_docs_expanded_df, manual_covenanted_docs_expanded_df]
    )

    # Drop parcel-level fields to get de-duped list of subjects
    all_covenanted_docs_df = all_covenanted_docs_expanded_df.drop(
        columns=[
            "mapped_address",
            "mapped_state",
            "mapped_parcel_pin",
        ]
    ).drop_duplicates(subset=["cov_type", "db_id"])

    # created group-by dfs of address, city, state, cnty_pin to deal with multiple parcels
    address_list = (
        all_covenanted_docs_expanded_df[["cov_type", "db_id", "mapped_address"]]
        .groupby(["cov_type", "db_id"])["mapped_address"]
        .apply(deduped_str_list)
        .reset_index(name="addresses")
    )

    city_list = (
        all_covenanted_docs_expanded_df[["cov_type", "db_id", "mapped_city"]]
        .groupby(["cov_type", "db_id"])["mapped_city"]
        .apply(deduped_str_list)
        .reset_index(name="cities")
    )

    state_list = (
        all_covenanted_docs_expanded_df[["cov_type", "db_id", "mapped_state"]]
        .groupby(["cov_type", "db_id"])["mapped_state"]
        .apply(deduped_str_list)
        .reset_index(name="state")
    )

    pin_list = (
        all_covenanted_docs_expanded_df[["cov_type", "db_id", "mapped_parcel_pin"]]
        .groupby(["cov_type", "db_id"])["mapped_parcel_pin"]
        .apply(deduped_str_list)
        .reset_index(name="cnty_pins")
    )

    # Merged groups of addresses back to de-duped list of docs
    all_covenanted_docs_df = (
        all_covenanted_docs_df.merge(address_list, how="left", on=["cov_type", "db_id"])
        .merge(city_list, how="left", on=["cov_type", "db_id"])
        .merge(state_list, how="left", on=["cov_type", "db_id"])
        .merge(pin_list, how="left", on=["cov_type", "db_id"])
    )

    first_image_url = all_covenanted_docs_df["web_image"].iloc[0]
    url_prefix = get_image_url_prefix(first_image_url)
    all_covenanted_docs_df["web_image"] = all_covenanted_docs_df["web_image"].apply(
        lambda x: get_full_url(url_prefix, x)
    )
    all_covenanted_docs_df["highlight_image"] = all_covenanted_docs_df[
        "highlight_image"
    ].apply(lambda x: get_full_url(url_prefix, x))
    all_covenanted_docs_df["deed_date"] = pd.to_datetime(
        all_covenanted_docs_df["deed_date"]
    )
    all_covenanted_docs_df["deed_year"] = all_covenanted_docs_df["deed_date"].dt.year

    return all_covenanted_docs_df[ALL_DOCS_ATTRIBUTES]


def build_discharge_df(workflow):

    DISCHARGE_ATTRIBUTES = [
        "db_id",
        "doc_num",
        "deed_year",
        "deed_date",
        "cov_text",
        "seller",
        "buyer",
        "add_cov",
        "block_cov",
        "lot_cov",
        "map_book",
        "map_page",
        "is_mapped",
        "addresses",
        "cities",
        "state",
        "cnty_pins",
        "manual_cx",
        "dt_updated",
        "main_image",
        "highlight_image",
        # 'image_ids',
    ]

    df = build_all_covenanted_docs_df(workflow)
    return df[DISCHARGE_ATTRIBUTES]


def build_metes_and_bounds_df(workflow, n_items=50):
    M_AND_B_ATTRIBUTES = [
        "doc_num",
        "deed_year",
        "deed_date",
        "is_mapped",
        "image_lookup",
        "web_image",
    ]
    df = build_all_covenanted_docs_df(workflow)
    df = df[df["match_type"] == "PD"]
    df.rename(columns={"main_image": "image_lookup"}, inplace=True)

    # Drop rows with blank web_image
    df.dropna(subset=["image_lookup"], inplace=True)

    if df.shape[0] > 0:
        sample_size = n_items if df.shape[0] > n_items else df.shape[0]
        df = df.sample(n=sample_size)[M_AND_B_ATTRIBUTES]
        return df
    return pd.DataFrame()


PARCEL_EXPORT_FIELDS_ORDERED = [
    "db_id",
    "workflow",
    "cnty_pin",
    "street_add",
    "city",
    "plat_name",
    "block",
    "lot",
    "bool_cov",
]


def build_parcel_gdf(workflow):
    parcels = (
        Parcel.objects.filter(workflow=workflow)
        .annotate(wkt_4326=AsWKT("geom_4326"), workflow_slug=F("workflow__slug"))
        .values(
            "id",
            "workflow_slug",
            "pin_primary",
            "street_address",
            "city",
            "plat_name",
            "block",
            "lot",
            "bool_covenant",
            "wkt_4326",
        )
    )

    parcels_df = pd.DataFrame(parcels)

    if parcels_df.shape[0] == 0:
        return gpd.GeoDataFrame(
            columns=PARCEL_EXPORT_FIELDS_ORDERED + ["geometry"], geometry="geometry"
        )

    parcels_df.rename(
        columns={
            "id": "db_id",
            "workflow_slug": "workflow",
            "pin_primary": "cnty_pin",
            "street_address": "street_add",
            "bool_covenant": "bool_cov",
            "wkt_4326": "geometry",
        },
        inplace=True,
    )

    parcels_df = parcels_df[PARCEL_EXPORT_FIELDS_ORDERED + ["geometry"]]

    parcels_df["geometry"] = gpd.GeoSeries.from_wkt(
        parcels_df["geometry"], crs="EPSG:4326"
    )

    return gpd.GeoDataFrame(parcels_df, geometry="geometry")


# Column-per-position rather than a dict per parcel: at ~167k parcels the
# repeated JSON keys cost more than the data does.
PARCEL_SEARCH_INDEX_FIELDS = [
    'db_id',
    'cnty_pin',
    'street_add',
    'city',
    'plat_name',
    'block',
    'lot',
    'bool_cov',
    'lon',
    'lat',
    'join_strings',
]


def build_parcel_search_index(workflow):
    '''A searchable index of every parcel in a workflow, for the map editor.

    Join strings come first in the row because they are what a covenant is
    matched to a parcel on, and they are not in the baked tiles at all.'''
    from apps.parcel.models import ParcelJoinCandidate

    join_strings_by_parcel = {}
    candidates = ParcelJoinCandidate.objects.filter(
        workflow=workflow
    ).values_list('parcel_id', 'join_string').iterator(chunk_size=10000)
    for parcel_id, join_string in candidates:
        if join_string:
            join_strings_by_parcel.setdefault(parcel_id, []).append(join_string)

    rows = []
    parcels = Parcel.objects.filter(workflow=workflow).annotate(
        centroid_json=AsGeoJSON(Centroid('geom_4326'))
    ).values(
        'id',
        'pin_primary',
        'street_address',
        'city',
        'plat_name',
        'block',
        'lot',
        'bool_covenant',
        'centroid_json',
    ).iterator(chunk_size=5000)

    for parcel in parcels:
        lon, lat = json.loads(parcel['centroid_json'])['coordinates']
        rows.append([
            parcel['id'],
            parcel['pin_primary'] or '',
            parcel['street_address'] or '',
            parcel['city'] or '',
            parcel['plat_name'] or '',
            parcel['block'] or '',
            parcel['lot'] or '',
            bool(parcel['bool_covenant']),
            # ~1m precision is plenty to fly the map to a parcel
            round(lon, 5),
            round(lat, 5),
            sorted(join_strings_by_parcel.get(parcel['id'], [])),
        ])

    return {
        'workflow': workflow.slug,
        'fields': PARCEL_SEARCH_INDEX_FIELDS,
        'parcels': rows,
    }


DRAWN_MATCH_TYPE = 'Custom drawn geometry'


def workflow_county(workflow):
    '''County name and FIPS for a workflow, taken from its parcels.

    Drawn shapes have no parcel to inherit these from, and workflows are
    county-scoped, so any parcel in the workflow answers for all of them.'''
    county = Parcel.objects.filter(workflow=workflow).values(
        'county_name', 'county_fips'
    ).first()
    if not county:
        return None, None
    return county['county_name'], county['county_fips']


def drawn_covenant_attrs(drawn_geometry):
    '''Flatten the covenant behind a drawn shape into CovenantedParcel columns.

    The parcel-derived path gets these from Parcel.covenant_objects, which
    annotates a parcel with its covenant. A drawn shape has no parcel, so the
    covenant's own values are used and the parcel-side columns stay empty.'''
    covenant = drawn_geometry.covenant
    cnty_name, cnty_fips = workflow_county(drawn_geometry.workflow)

    attrs = {
        'workflow': drawn_geometry.workflow,
        'parcel': None,
        'drawn_geometry': drawn_geometry,
        'cnty_name': cnty_name,
        'cnty_fips': cnty_fips,
        'cnty_pin': '',
        'match_type': DRAWN_MATCH_TYPE,
        'manual_cx': True,
        'dt_updated': datetime.date.today(),
        'geom_4326': drawn_geometry.geom_4326,
    }

    if drawn_geometry.zooniverse_subject_id:
        attrs.update({
            'cov_type': 'zooniverse',
            'doc_num': covenant.deedpage_doc_num,
            'deed_date': covenant.deed_date_final,
            'deed_year': year_or_null(covenant.deed_date_final),
            'cov_text': covenant.covenant_text_final,
            'seller': covenant.seller_final,
            'buyer': covenant.buyer_final,
            'street_add': covenant.street_address_final,
            'city': covenant.city_final,
            'add_cov': covenant.addition_final,
            'block_cov': covenant.block_final,
            'lot_cov': covenant.lot_final,
            'map_book': covenant.map_book_final,
            'map_page': covenant.map_book_page_final,
            'join_strgs': join_strings_to_str(covenant.join_candidates),
            'zn_subj_id': covenant.zoon_subject_id,
            'zn_dt_ret': covenant.dt_retired,
            'med_score': covenant.median_score,
        })
    else:
        attrs.update({
            'cov_type': 'manual',
            'doc_num': covenant.doc_num,
            'deed_date': covenant.deed_date,
            'deed_year': year_or_null(covenant.deed_date),
            'cov_text': covenant.covenant_text,
            'seller': covenant.seller,
            'buyer': covenant.buyer,
            'city': covenant.city,
            'add_cov': covenant.addition,
            'block_cov': covenant.block,
            'lot_cov': covenant.lot,
            'map_book': covenant.map_book,
            'map_page': covenant.map_book_page,
            'join_strgs': join_strings_to_str(covenant.join_candidates),
        })

    return attrs


def save_flat_drawn_covenant(drawn_geometry, trigger_bake=True):
    '''Rebuild the flat CovenantedParcel row for one drawn shape.

    Parcel-derived rows are rebuilt in bulk off a parcel queryset, which cannot
    reach a row with no parcel, so drawn shapes refresh themselves here.'''
    from apps.parcel.models import CovenantedParcel

    CovenantedParcel.objects.filter(drawn_geometry=drawn_geometry).delete()
    covenanted_parcel = CovenantedParcel.objects.create(
        **drawn_covenant_attrs(drawn_geometry)
    )

    if trigger_bake and drawn_geometry.workflow is not None:
        from apps.parcel.utils.pmtiles_utils import trigger_pmtiles_export
        trigger_pmtiles_export(drawn_geometry.workflow)

    return covenanted_parcel
