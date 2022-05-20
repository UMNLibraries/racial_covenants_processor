import os
import json
import datetime
import tempfile
import pandas as pd
import geopandas as gpd

from django.core.management.base import BaseCommand
from django.contrib.gis.db.models.functions import AsWKT
from django.core.files.base import File
from django.conf import settings

from apps.parcel.models import Parcel, GeoJSONExport
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''geojson exporter to either s3 or local file'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        parser.add_argument('-l', '--local', action='store_true',
                            help='Save to local geojson in "main_exports" dir, rather than Django object/S3')

    def build_gdf(self, workflow):
        joined_covenants = Parcel.covenant_objects.filter(
            workflow=workflow
        ).annotate(
            wkt_4326=AsWKT('geom_4326')
        ).values(
            'workflow',
            'county_name',
            'county_fips',

            'deed_date',
            'seller',
            'buyer',
            'covenant_text',

            'zoon_subject_id',
            'zoon_dt_retired',
            'image_ids',
            'median_score',
            'manual_cx',
            'match_type',

            'street_address',
            'city',
            'state',
            'zip_code',

            'addition_cov',
            'lot_cov',
            'block_cov',

            'pin_primary',
            'plat_name',
            'block',
            'lot',
            'phys_description',

            'plat',

            'date_updated',

            'wkt_4326'
        )

        covenants_df = pd.DataFrame(joined_covenants)
        covenants_df.rename(columns={
            'id': 'db_id',
            'plat_name': 'addition_modern',
            'block': 'block_modern',
            'lot': 'lot_modern',
            'phys_description': 'phys_description_modern',
            'wkt_4326': 'geometry'
        }, inplace=True)

        covenants_df['image_ids'] = covenants_df['image_ids'].apply(lambda x: json.dumps(x))

        covenants_df['geometry'] = gpd.GeoSeries.from_wkt(
            covenants_df['geometry'], crs='EPSG:4326')

        covenants_gdf = gpd.GeoDataFrame(
            covenants_df, geometry='geometry')

        return covenants_gdf

    def save_geojson_local(self, gdf, version_slug, schema):
        out_geojson = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{version_slug}.geojson")
        gdf.to_file(out_geojson, schema=schema, index=False)

        return out_geojson

    def save_geojson_model(self, gdf, version_slug, workflow, created_at, schema):
        # Convert to shapefile and serve it to the user
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_file_path = os.path.join(tmp_dir, f'{version_slug}.geojson')
            # df.to_geojson(tmp_file_path, index=False)
            gdf.to_file(tmp_file_path, schema=schema, index=False)

            geojson_export_obj = GeoJSONExport(
                workflow=workflow,
                covenant_count=gdf.shape[0],
                created_at = created_at
            )

            # Using File
            with open(tmp_file_path, 'rb') as f:
                geojson_export_obj.geojson.save(f'{version_slug}.geojson', File(f))
            geojson_export_obj.save()
            return geojson_export_obj

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            covenants_gdf = self.build_gdf(workflow)

            # Shapefiles don't like datetime format, so specify date in manual schema
            schema = gpd.io.file.infer_schema(covenants_gdf)
            schema['properties']['deed_date'] = 'date'
            schema['properties']['date_updated'] = 'date'
            schema['properties']['zoon_dt_retired'] = 'date'

            print(covenants_gdf)

            now = datetime.datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%m')
            version_slug = f"{workflow.slug}_covenants_{timestamp}"

            if kwargs['local']:
                geojson_local = self.save_geojson_local(covenants_gdf, version_slug, schema)
            else:
                # Save to zipped shp in Django storages/model
                geojson_export_obj = self.save_geojson_model(covenants_gdf, version_slug, workflow, now, schema)
