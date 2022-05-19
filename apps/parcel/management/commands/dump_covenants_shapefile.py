import os
import datetime
import tempfile
import pandas as pd
import geopandas as gpd
from shapely import wkt
from zipfile import ZipFile

from django.core.management.base import BaseCommand
from django.core.files.base import File
from django.contrib.gis.db.models.functions import AsWKT
from django.conf import settings

from apps.parcel.models import ShpExport
from apps.parcel.models import Parcel
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Attempt to auto-join covenants to modern parcels using current values'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        parser.add_argument('-l', '--local', action='store_true',
                            help='Save to local un-zipped shp in "main_exports" dir, rather than Django object/S3')

    def build_gdf(self, workflow):
        joined_covenants = Parcel.covenant_objects.filter(
            workflow=workflow
        ).annotate(
            wkt_4326=AsWKT('geom_4326')
        ).values(
            'id',
            'workflow',
            'county_name',
            'county_fips',

            'deed_date',
            'seller',
            'buyer',
            'covenant_text',

            'zoon_subject_id',
            'zoon_dt_retired',
            # 'image_ids',
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

        covenants_df['geometry'] = gpd.GeoSeries.from_wkt(
            covenants_df['geometry'], crs='EPSG:4326')

        covenants_geo_df = gpd.GeoDataFrame(
            covenants_df, geometry='geometry')

        return covenants_geo_df

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

            covenants_geo_df = self.build_gdf(workflow)

            # Shapefiles don't like datetime format, so specify date in manual schema
            schema = gpd.io.file.infer_schema(covenants_geo_df)
            schema['properties']['deed_date'] = 'date'
            schema['properties']['date_updated'] = 'date'
            schema['properties']['zoon_dt_retired'] = 'date'

            print(covenants_geo_df)

            now = datetime.datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%m')
            version_slug = f"{workflow.slug}_covenants_{timestamp}"

            if kwargs['local']:
                shp_local = self.save_shp_local(covenants_geo_df, version_slug, schema)
            else:
                # Save to zipped shp in Django storages/model
                shp_export_obj = self.generate_zip_tmp(covenants_geo_df, version_slug, workflow, now, schema)
