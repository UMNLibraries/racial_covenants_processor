import os
import datetime
import pandas as pd
import geopandas as gpd
from shapely import wkt

from django.core.management.base import BaseCommand
from django.contrib.gis.db.models.functions import AsWKT
from django.conf import settings

from zoon.models import ZooniverseWorkflow, ZooniverseSubject
from zoon.utils.zooniverse_config import get_workflow_version


class Command(BaseCommand):
    '''Attempt to auto-join covenants to modern parcels using current values'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            # This config info comes from local_settings, generally.
            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            self.batch_dir = os.path.join(
                settings.BASE_DIR, 'data', 'zooniverse_exports', self.batch_config['panoptes_folder'])

            # Get workflow version from config yaml
            workflow_version = get_workflow_version(
                self.batch_dir, self.batch_config['config_yaml'])

            workflow = ZooniverseWorkflow.objects.get(
                workflow_name=workflow_name, version=workflow_version)

            joined_covenants = ZooniverseSubject.objects.filter(
                geom_union_4326__isnull=False
            ).annotate(
                wkt_4326=AsWKT('geom_union_4326')
            ).values(
                'id',
                'covenant_text_final',
                'addition_final',
                'lot_final',
                'block_final',
                'deed_date_final',
                'median_score',
                'bool_manual_correction',
                'wkt_4326'
            )

            covenants_df = pd.DataFrame(joined_covenants)
            covenants_df.to_csv(os.path.join(
                settings.BASE_DIR, 'data', 'shp_test.csv'), index=False)

            covenants_df.rename(columns={
                'id': 'db_id',
                'covenant_text_final': 'covenant_text',
                'addition_final': 'addition',
                'lot_final': 'lot',
                'block_final': 'block',
                'deed_date_final': 'deed_date',
                'bool_manual_correction': 'manual_cx',
                'wkt_4326': 'geometry'
            }, inplace=True)

            covenants_df['geometry'] = gpd.GeoSeries.from_wkt(
                covenants_df['geometry'], crs='EPSG:4326')

            covenants_geo_df = gpd.GeoDataFrame(
                covenants_df, geometry='geometry')

            # Shapefiles don't like datetime format, so specify date in manual schema
            schema = gpd.io.file.infer_schema(covenants_geo_df)
            schema['properties']['deed_date'] = 'date'

            print(covenants_geo_df)

            version_slug = f"{workflow.slug}_covenants_{datetime.datetime.now().date()}"
            os.makedirs(os.path.join(
                settings.BASE_DIR, 'data', 'main_exports', version_slug), exist_ok=True)
            out_shp = os.path.join(
                settings.BASE_DIR, 'data', 'main_exports', version_slug, f"{version_slug}.shp")
            covenants_geo_df.to_file(out_shp, schema=schema, index=False)
