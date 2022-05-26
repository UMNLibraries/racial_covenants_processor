import os
import json
import datetime
import tempfile
import geopandas as gpd

from django.core.management.base import BaseCommand
from django.core.files.base import File
from django.conf import settings

from apps.parcel.models import GeoJSONExport
from apps.parcel.utils.export_utils import build_gdf
from apps.zoon.models import MATCH_TYPE_OPTIONS
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''geojson exporter to either s3 or local file'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        parser.add_argument('-l', '--local', action='store_true',
                            help='Save to local geojson in "main_exports" dir, rather than Django object/S3')

    def save_geojson_local(self, gdf, version_slug, schema):
        out_geojson = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{version_slug}.geojson")
        gdf.to_file(out_geojson, schema=schema, index=False)

        return out_geojson

    def save_geojson_model(self, gdf, version_slug, workflow, created_at, schema):
        # export to .geojson temp file and serve it to the user
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

            covenants_gdf = build_gdf(workflow)

            # Shapefiles don't like datetime format, so specify date in manual schema
            schema = gpd.io.file.infer_schema(covenants_gdf)
            schema['properties']['deed_date'] = 'date'
            schema['properties']['dt_updated'] = 'date'
            schema['properties']['zn_dt_ret'] = 'date'

            print(covenants_gdf)

            now = datetime.datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%M')
            version_slug = f"{workflow.slug}_covenants_{timestamp}"

            if kwargs['local']:
                geojson_local = self.save_geojson_local(covenants_gdf, version_slug, schema)
            else:
                # Save to geojson in Django storages/model
                geojson_export_obj = self.save_geojson_model(covenants_gdf, version_slug, workflow, now, schema)
