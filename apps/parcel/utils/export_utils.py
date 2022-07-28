import pandas as pd
import geopandas as gpd

from django.contrib.gis.db.models.functions import AsWKT

from apps.parcel.models import Parcel
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
        'cnty_pin',

        'deed_date',
        'seller',
        'buyer',
        'cov_type',
        'cov_text',

        'zn_subj_id',
        'zn_dt_ret',
        'image_ids',
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

        'dt_updated',
        'wkt_4326'
    )

    covenants_df = pd.DataFrame(joined_covenants)

    covenants_df['deed_year'] = pd.DatetimeIndex(covenants_df['deed_date']).year
    covenants_df['join_strgs'] = covenants_df['join_candidates'].apply(lambda x: ';'.join([jc['join_string'] for jc in x]))

    MATCH_TYPES = MATCH_TYPE_OPTIONS + MANUAL_COV_OPTIONS
    covenants_df['match_type'] = covenants_df['match_type'].apply(lambda x: [mt[1] for mt in MATCH_TYPES if mt[0] == x][0] if x is not None else 'Automatic match')

    covenants_df['image_ids'] = covenants_df['image_ids'].apply(lambda x: ','.join([img for img in x]))

    # Currently blank fields in existing workflows
    covenants_df[[
        'doc_num',
        'exec_date',
        'geocd_addr',
        'geocd_dist',
    ]] = ''

    covenants_df.drop(columns=['join_candidates'], inplace=True)

    covenants_df.rename(columns={
        'id': 'db_id',
        'plat__pk': 'plat_dbid',
        'wkt_4326': 'geometry'
    }, inplace=True)

    covenants_df = covenants_df[EXPORT_FIELDS_ORDERED + ['geometry']]

    covenants_df['geometry'] = gpd.GeoSeries.from_wkt(
        covenants_df['geometry'], crs='EPSG:4326')

    covenants_geo_df = gpd.GeoDataFrame(
        covenants_df, geometry='geometry')

    return covenants_geo_df
