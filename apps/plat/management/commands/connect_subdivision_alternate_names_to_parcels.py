from django.core.management.base import BaseCommand
from django.conf import settings

from apps.plat.models import Subdivision, SubdivisionAlternateName
from apps.parcel.models import Parcel
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Connect SubdivisionAlternateName objects to parcels'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            print(
                f'Collecting Parcel records that match SubdivisionAlternateNames...')
            for san in SubdivisionAlternateName.objects.filter(
                workflow=workflow
            ):
                parcel_matches = Parcel.objects.filter(
                    workflow=workflow,
                    plat_standardized=san.alternate_name_standardized
                )
                parcel_matches.update(subdivision_spatial=san.subdivision)
