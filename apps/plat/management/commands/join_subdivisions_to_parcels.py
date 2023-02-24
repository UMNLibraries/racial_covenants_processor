from django.conf import settings
from django.core.management.base import BaseCommand

from apps.parcel.models import Parcel
from apps.zoon.utils.zooniverse_config import get_workflow_obj

class Command(BaseCommand):
    '''Spatially join a workflow's Parcel objects to a Subdivision GIS layer'''
    batch_config = None  # Set in handle
    shp_dir = None

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
            workflow = get_workflow_obj(workflow_name)

            print('Finding matching subdivisions by spatial join...')

            parcels_with_subs = Parcel.objects.raw('''SELECT
              parcels.id AS id,
              parcels.join_description AS join_description,
              subdivisions.name AS subdivision_name,
              subdivisions.id AS subdivision_spatial_id
            FROM parcel_parcel AS parcels
            JOIN plat_subdivision AS subdivisions
            ON ST_Contains(subdivisions.geom_4326, ST_Centroid(parcels.geom_4326))
            WHERE parcels.workflow_id = %s;''', [workflow.id])

            parcels_with_subs_list = list(parcels_with_subs)
            # for p in parcels_with_subs[:10]:
            #     print(p.id, p.join_description, p.subdivision_name, p.subdivision_id)

            print(f'Updating {len(parcels_with_subs_list)} parcels ...')
            Parcel.objects.bulk_update(
                parcels_with_subs_list, ['subdivision_spatial_id'], batch_size=5000)
