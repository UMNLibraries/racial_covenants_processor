import pandas as pd
import geopandas as gpd

from django.contrib.gis.db.models.functions import AsWKT

from apps.parcel.models import Parcel
from apps.zoon.models import ZooniverseSubject, ManualCovenant
from apps.zoon.models import MATCH_TYPE_OPTIONS, MANUAL_COV_OPTIONS


EXPORT_FIELDS_ORDERED = [
    'db_id',
    'workflow',
    'cnty_name',
    'cnty_fips',
    'doc_num',
    'deed_year',
    'deed_date',
    'exec_date',
    'cov_text',
    'seller',
    'buyer',
    'street_add',
    'city',
    'state',
    'zip_code',
    'add_cov',
    'block_cov',
    'lot_cov',
    'cnty_pin',
    'add_mod',
    'block_mod',
    'lot_mod',
    'ph_dsc_mod',
    'join_strgs',
    'geocd_addr',
    'geocd_dist',
    'cov_type',
    'match_type',
    'manual_cx',
    'dt_updated',
    'zn_subj_id',
    'zn_dt_ret',
    'image_ids',
    'med_score',
    'plat_dbid',
    'subd_dbid',
]


def build_gdf(workflow):
    joined_covenants = Parcel.covenant_objects.filter(
        workflow=workflow
    ).annotate(
        wkt_4326=AsWKT('geom_4326')
    ).values(
        'id',
        'workflow',
        'cnty_name',
        'cnty_fips',
        'doc_num',
        'cnty_pin',

        'deed_date',
        'seller',
        'buyer',
        'cov_type',
        'cov_text',

        'zn_subj_id',
        'zn_dt_ret',
        # 'image_ids',

        'deed_page_1',
        'deed_page_2',
        'deed_page_3',

        'med_score',
        'manual_cx',
        'match_type',
        'join_candidates',

        'street_add',
        'city',
        'state',
        'zip_code',

        'add_cov',
        'block_cov',
        'lot_cov',

        'add_mod',
        'block_mod',
        'lot_mod',
        'ph_dsc_mod',

        'plat__pk',
        'subdivision_spatial__pk',

        'dt_updated',
        'wkt_4326'
    )

    covenants_df = pd.DataFrame(joined_covenants)

    covenants_df['deed_year'] = pd.DatetimeIndex(covenants_df['deed_date']).year
    covenants_df['join_strgs'] = covenants_df['join_candidates'].apply(lambda x: ';'.join([jc['join_string'] for jc in x]))

    MATCH_TYPES = MATCH_TYPE_OPTIONS + MANUAL_COV_OPTIONS

    # TEMP TEMP TEMP until bug #90 closed
    covenants_df = covenants_df[covenants_df['match_type'] != '']

    # print(MATCH_TYPES)
    # print(covenants_df[covenants_df['match_type'] == ''][['add_cov', 'block_cov', 'join_strgs', 'add_mod', 'ph_dsc_mod']])
    covenants_df['match_type'] = covenants_df['match_type'].apply(lambda x: [mt[1] for mt in MATCH_TYPES if mt[0] == x][0] if x is not None else 'Automatic match')

    covenants_df['image_ids'] = covenants_df[['deed_page_1', 'deed_page_2', 'deed_page_3']].apply(lambda x: ','.join(x.dropna()), axis=1)

    # covenants_df['image_ids'] = covenants_df['image_ids'].apply(lambda x: ','.join([img if img else '' for img in x]))

    # Currently blank fields in existing workflows
    covenants_df[[
        # 'doc_num',
        'exec_date',
        'geocd_addr',
        'geocd_dist',
    ]] = ''

    covenants_df.drop(columns=['join_candidates', 'deed_page_1', 'deed_page_2', 'deed_page_3'], inplace=True)

    covenants_df.rename(columns={
        'id': 'db_id',
        'plat__pk': 'plat_dbid',
        'subdivision_spatial__pk': 'subd_dbid',
        'wkt_4326': 'geometry'
    }, inplace=True)

    covenants_df = covenants_df[EXPORT_FIELDS_ORDERED + ['geometry']]

    covenants_df['geometry'] = gpd.GeoSeries.from_wkt(
        covenants_df['geometry'], crs='EPSG:4326')

    covenants_geo_df = gpd.GeoDataFrame(
        covenants_df, geometry='geometry')

    return covenants_geo_df


def build_unmapped_df(workflow, cnty_name=None, cnty_fips=None):
    unmapped_covenants = ZooniverseSubject.unmapped_objects.filter(
        workflow=workflow
    ).values(
        'id',
        'workflow',
        'doc_num',
        'deed_date_final',
        'seller_final',
        'buyer_final',
        'cov_type',
        'cov_text',
        'zn_subj_id',
        'zn_dt_ret',
        'image_ids',
        # 'deed_page_1',
        # 'deed_page_2',
        # 'deed_page_3',
        'med_score',
        'manual_cx',
        'match_type',
        'join_candidates',
        'add_cov',
        'block_cov',
        'lot_cov',
        'city_cov',
        'dt_updated',

    )

    unmapped_df = pd.DataFrame(unmapped_covenants)
    unmapped_df.rename(columns={
        'deed_date_final': 'deed_date',
        'seller_final': 'seller',
        'buyer_final': 'buyer',
    }, inplace=True)

    # covenants_df['image_ids'] = covenants_df[[
    #     'deed_page_1', 'deed_page_2', 'deed_page_3'
    # ]].apply(lambda x: ','.join(x.dropna()), axis=1)

    unmapped_df['cnty_name'] = cnty_name
    unmapped_df['cnty_fips'] = cnty_fips
    # unmapped_df['match_type'] = 'unmapped'

    return unmapped_df


def build_validation_df(workflow):
    '''In contrast to mapped covenants, this is all about Zooniverse stuff, so
    build a DF off the ZooniverseSubject
    as opposed to Parcel.covenant_objects'''

    VALIDATION_ATTRS = [
        'id',
        'workflow',
        'doc_num',
        'deed_date_final',
        # 'seller_final',
        # 'buyer_final',
        'cov_type',
        'cov_text',
        'zn_subj_id',
        'zn_dt_ret',
        'resp_count',
        'med_score',
        'cov_score',
        'hand_score',
        'mtype_score',
        'text_score',
        'add_score',
        'lot_score',
        'block_score',
        'city_score',
        'sell_score',
        'buy_score',
        'manual_cx',
        'match_type',
        'join_candidates',
        'add_cov',
        'block_cov',
        'lot_cov',
        'city_cov',
        'dt_updated',
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
        return '; '.join(uniques)
    return ''


def build_all_covenanted_docs_df(workflow):
    '''Export all copies of covenanted documents from both ZooniverseSubject and ManualCovenant'''

    ALL_DOCS_ATTRIBUTES = [
        'workflow',
        'cov_type',
        'db_id',
        'doc_num',
        'deed_year',
        'deed_date',
        'cov_text',
        'seller',
        'buyer',
        'add_cov',
        'block_cov',
        'lot_cov',
        'is_mapped',
        'addresses',
        'cities',
        'state',
        'cnty_pins',
        'join_strgs',
        'match_type',
        'manual_cx',
        'dt_updated',
        'zn_subj_id',
        'zn_dt_ret',
        'image_ids',
        'med_score',
    ]

    zoon_covenanted_subjects = ZooniverseSubject.all_covenanted_docs_objects.filter(
        workflow=workflow
    ).values(
        'db_id',
        'workflow',
        'is_mapped',
        'deed_date_final',  # Need to rename with pd
        'cov_text',
        'image_ids',
        'zn_subj_id',
        'zn_dt_ret',
        'med_score',
        'manual_cx',
        'add_cov',
        'block_cov',
        'lot_cov',
        'join_strgs',
        'mapped_address',
        'mapped_city',
        'mapped_state',
        'mapped_parcel_pin',
        'seller_final',  # Need to rename with pd
        'buyer_final',  # Need to rename with pd
        'dt_updated',
        'doc_num',
        'cov_type',
        'match_type_final',  # Need to rename with pd =Value('unmapped')
    )

    # TK
    all_manual_covenants = ManualCovenant.all_covenanted_docs_objects.filter(
        workflow=workflow
    ).values(
        'db_id',
        'workflow',
        'is_mapped',
        'deed_date',
        'cov_text',
        # 'image_ids',  # Need to set to null with pd
        'zn_subj_id',
        'zn_dt_ret',
        'med_score',
        'manual_cx',
        'add_cov',
        'block_cov',
        'lot_cov',
        'join_strgs',
        'mapped_address',
        'mapped_city',
        'mapped_state',
        'mapped_parcel_pin',
        'seller',
        'buyer',
        'dt_updated',
        'doc_num',
        'cov_type', # Need to rename with pd to match_type
        # 'cov_type_manual', # Need to rename with pd to cov_type (janky!)
        # 'match_type',  # Need to rename with pd =Value('unmapped')
    )


    # TODO: fix image ids

    # Convert to pandas DF 
    zoon_covenanted_docs_expanded_df = pd.DataFrame(zoon_covenanted_subjects)
    zoon_covenanted_docs_expanded_df.rename(columns={
        'deed_date_final': 'deed_date',
        'seller_final': 'seller',
        'buyer_final': 'buyer',
        'city_final': 'city',
        'match_type_final': 'match_type',
    }, inplace=True)

    manual_covenanted_docs_expanded_df = pd.DataFrame(all_manual_covenants)
    
    manual_covenanted_docs_expanded_df.rename(
        columns={'cov_type': 'match_type'}, inplace=True
    )
    manual_covenanted_docs_expanded_df['image_ids'] = ''
    manual_covenanted_docs_expanded_df['cov_type'] = 'manual'

    all_covenanted_docs_expanded_df = pd.concat([zoon_covenanted_docs_expanded_df, manual_covenanted_docs_expanded_df])

    # Drop parcel-level fields to get de-duped list of subjects
    all_covenanted_docs_df = all_covenanted_docs_expanded_df.drop(columns=[
        'mapped_address',
        'mapped_state',
        'mapped_parcel_pin',
    ]).drop_duplicates(subset=["cov_type", "db_id"])

    # created group-by dfs of address, city, state, cnty_pin to deal with multiple parcels
    address_list = all_covenanted_docs_expanded_df[[
        'cov_type',
        'db_id',
        'mapped_address'
    ]].groupby(["cov_type", "db_id"])['mapped_address'].apply(deduped_str_list).reset_index(name='addresses')

    city_list = all_covenanted_docs_expanded_df[[
        'cov_type',
        'db_id',
        'mapped_city'
    ]].groupby(["cov_type", "db_id"])['mapped_city'].apply(deduped_str_list).reset_index(name='cities')

    state_list = all_covenanted_docs_expanded_df[[
        'cov_type',
        'db_id',
        'mapped_state'
    ]].groupby(["cov_type", "db_id"])['mapped_state'].apply(deduped_str_list).reset_index(name='state')

    pin_list = all_covenanted_docs_expanded_df[[
        'cov_type',
        'db_id',
        'mapped_parcel_pin'
    ]].groupby(["cov_type", "db_id"])['mapped_parcel_pin'].apply(deduped_str_list).reset_index(name='cnty_pins')

    # Merged groups of addresses back to de-duped list of docs
    all_covenanted_docs_df = all_covenanted_docs_df.merge(
        address_list,
        how="left",
        on=["cov_type", "db_id"]
    ).merge(
        city_list,
        how="left",
        on=["cov_type", "db_id"]
    ).merge(
        state_list,
        how="left",
        on=["cov_type", "db_id"]
    ).merge(
        pin_list,
        how="left",
        on=["cov_type", "db_id"]
    )

    all_covenanted_docs_df['deed_date'] = pd.to_datetime(all_covenanted_docs_df['deed_date'])
    all_covenanted_docs_df['deed_year'] = all_covenanted_docs_df['deed_date'].dt.year

    return all_covenanted_docs_df[ALL_DOCS_ATTRIBUTES]
