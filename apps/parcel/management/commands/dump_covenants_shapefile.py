import os
import json
import datetime
import tempfile
import geopandas as gpd
from zipfile import ZipFile

from django.core.management.base import BaseCommand
from django.core.files.base import File
from django.conf import settings

from apps.parcel.models import ShpExport
from apps.parcel.utils.export_utils import build_gdf
from apps.zoon.models import MATCH_TYPE_OPTIONS
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Attempt to auto-join covenants to modern parcels using current values'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        parser.add_argument('-l', '--local', action='store_true',
                            help='Save to local un-zipped shp in "main_exports" dir, rather than Django object/S3')

    def save_shp_local(self, gdf, version_slug, schema):

        os.makedirs(os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', version_slug), exist_ok=True)
        out_shp = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', version_slug, f"{version_slug}.shp")
        gdf.to_file(out_shp, schema=schema, index=False)

        return out_shp

    def generate_zip_tmp(self, gdf, version_slug, workflow, created_at, schema):
        # Convert to shapefile and serve it to the user
        with tempfile.TemporaryDirectory() as tmp_dir:

            # Export gdf as shapefile
            gdf.to_file(os.path.join(tmp_dir, f'{version_slug}.shp'), schema=schema, index=False, driver='ESRI Shapefile')

            # Zip the exported files to a single file
            tmp_zip_file_name = f'{version_slug}.zip'
            tmp_zip_file_path = f"{tmp_dir}/{tmp_zip_file_name}"
            tmp_zip_obj = ZipFile(tmp_zip_file_path, 'w')

            for file in os.listdir(tmp_dir):
                if file != tmp_zip_file_name:
                    tmp_zip_obj.write(os.path.join(tmp_dir, file), file)

            tmp_zip_obj.close()

            shp_export_obj = ShpExport(
                workflow=workflow,
                covenant_count=gdf.shape[0],
                created_at = created_at
            )

            # Using File
            with open(tmp_zip_file_path, 'rb') as f:
                shp_export_obj.shp_zip.save(f'{version_slug}.zip', File(f))
            shp_export_obj.save()
            return shp_export_obj

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            covenants_geo_df = build_gdf(workflow)

            # Shapefiles don't like datetime format, so specify date in manual schema
            schema = gpd.io.file.infer_schema(covenants_geo_df)
            schema['properties']['deed_date'] = 'date'
            schema['properties']['dt_updated'] = 'date'
            schema['properties']['zn_dt_ret'] = 'date'

            print(covenants_geo_df)

            now = datetime.datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%M')
            version_slug = f"{workflow.slug}_covenants_{timestamp}"

            if kwargs['local']:
                shp_local = self.save_shp_local(covenants_geo_df, version_slug, schema)
            else:
                # Save to zipped shp in Django storages/model
                shp_export_obj = self.generate_zip_tmp(covenants_geo_df, version_slug, workflow, now, schema)
