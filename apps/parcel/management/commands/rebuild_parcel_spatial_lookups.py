from django.core.management.base import BaseCommand
from django.conf import settings

from apps.parcel.models import Parcel, ParcelJoinCandidate
from apps.parcel.utils.parcel_utils import get_all_parcel_options
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Download and load a county parcel shapefile'''
    batch_config = None  # Set in handle
    shp_dir = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def build_parcel_spatial_lookups(self, workflow):
        print("Clearing old ParcelJoinCandidate objects...")
        ParcelJoinCandidate.objects.filter(workflow=workflow).delete()

        print('Building parcel spatial lookup options...')
        join_cands = []
        for parcel in Parcel.objects.filter(
            workflow=workflow
        ).exclude(lot__isnull=True).defer('geom_4326', 'orig_data'):
            # First parse parcel's default addition
            candidates, metadata = get_all_parcel_options(parcel)
            for c in candidates:
                # parcel_spatial_lookup[c['join_string']] = c
                join_cands.append(ParcelJoinCandidate(
                    workflow=workflow,
                    parcel=parcel,
                    plat_name_standardized=parcel.plat_standardized,
                    join_string=c['join_string'],
                    metadata=c['parcel_metadata']
                ))

        ParcelJoinCandidate.objects.bulk_create(join_cands, batch_size=5000)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            # This config info comes from local_settings, generally.
            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            workflow = get_workflow_obj(workflow_name)

            self.build_parcel_spatial_lookups(workflow)
