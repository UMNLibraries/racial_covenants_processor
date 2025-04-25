import pandas as pd
import geopandas as gpd

from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon

from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings
from django.contrib.gis.db.models.aggregates import Union
from django.contrib.gis.db.models.functions import AsWKT, MakeValid

from apps.plat.models import Subdivision
from apps.parcel.models import Parcel
from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.plat.utils.plat_utils import standardize_subdivisions

from django.db import connection


class Command(BaseCommand):
    '''Download and load a county parcel shapefile'''
    batch_config = None  # Set in handle
    shp_dir = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        
    # def get_groups_sql(self, workflow):
    #     '''Fair to say this did not work performantly, though this DB is not well tuned'''
    #     with connection.cursor() as cursor:
    #         cursor.execute("""
    #             SELECT plat_name,
    #             ST_ConcaveHull(
    #                 ST_MakeValid(
    #                     ST_Union(
    #                         geom_4326
    #                     )
    #                 ), 0.5
    #             ) AS hull_geom_4326
    #             FROM parcel_parcel
    #             WHERE workflow_id = %s
    #             AND plat_name IS NOT NULL
    #             GROUP BY plat_name
    #         """, [workflow.id])
    #         rows = cursor.fetchall()

    #         return rows
    #     return False

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            # This config info comes from local_settings, generally.
            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            workflow = get_workflow_obj(workflow_name)

            grouped_parcels = Parcel.objects.filter(
                workflow=workflow,
                plat_name__isnull=False
            ).values(
                'plat_name'
            ).annotate(
                geom_4326=AsWKT(MakeValid(Union('geom_4326')))
            ).order_by(
                'plat_name'
            )

            print(grouped_parcels.count())

            grouped_df = pd.DataFrame(grouped_parcels)
            gs = gpd.GeoSeries.from_wkt(grouped_df['geom_4326'])
            grouped_gdf = gpd.GeoDataFrame(grouped_df.drop(columns=['geom_4326']), geometry=gs, crs="EPSG:4326")
            grouped_gdf['concave_hull'] = grouped_gdf['geometry'].concave_hull()
            grouped_gdf.set_geometry('concave_hull', drop=True)

            grouped_gdf["concave_hull"] = [MultiPolygon([feature]) if isinstance(feature, Polygon) else feature for feature in grouped_gdf["concave_hull"]]

            print(grouped_gdf)

            objs = []
            obj_count = 0

            for index, row in grouped_gdf.iterrows():

                subdivision = Subdivision(
                    workflow=workflow,
                    name=row['plat_name'],
                    orig_filename="Generated from parcels",
                    geom_4326 = row['concave_hull'].wkt
                )
                print(subdivision)

                objs.append(subdivision)
                obj_count += 1

                if obj_count % 10000 == 0:
                    Subdivision.objects.bulk_create(objs)
                    print(f'Saved {obj_count} Subdivision records...')
                    objs = []

            Subdivision.objects.bulk_create(objs)
            print(f'Saved {obj_count} Subdivision records.')

            standardize_subdivisions(workflow)
            management.call_command(
                'join_subdivisions_to_parcels', workflow=workflow_name)
            management.call_command(
                'rebuild_parcel_spatial_lookups', workflow=workflow_name)
