from django.core.management.base import BaseCommand

from apps.parcel.models import Parcel, CovenantedParcel

from apps.parcel.utils.export_utils import save_flat_covenanted_parcels
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Refresh CovenantedParcel objects for workflow'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def save_flattened_covenants(self, workflow):
        # Do a more broad deletion to find any stragglers
        print("Deleting old CovenantedParcel records from this workflow...")
        CovenantedParcel.objects.filter(workflow=workflow).delete()

        print("Creating CovenantedParcel records from this workflow...")
        matched_parcels = Parcel.objects.filter(workflow=workflow, bool_covenant=True)
        flat_covenants = save_flat_covenanted_parcels(matched_parcels)

        if flat_covenants:
            print(f"{flat_covenants.count()} CovenantedParcel objects saved.")
            return flat_covenants
        return False

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            self.save_flattened_covenants(workflow)
