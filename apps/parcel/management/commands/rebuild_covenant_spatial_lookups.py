from django.core.management.base import BaseCommand
from django.conf import settings

from apps.parcel.utils.parcel_utils import gather_all_covenant_candidates, gather_all_manual_covenant_candidates
from apps.zoon.models import ZooniverseWorkflow, ZooniverseSubject, ManualCovenant
from apps.zoon.utils.zooniverse_config import get_workflow_obj

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
            workflow = get_workflow_obj(workflow_name)

            print("Updating ZooniverseSubject join candidates...")
            # Get all possible covenant lot candidaetes to join
            subjects = ZooniverseSubject.objects.filter(
                workflow=workflow,
                bool_covenant_final=True
            )
            for subject in subjects:
                subject.join_candidates = gather_all_covenant_candidates(subject)
            ZooniverseSubject.objects.bulk_update(subjects, fields=['join_candidates'], batch_size=5000)

            print("Updating ManualCovenant join candidates...")
            # Get all possible covenant lot candidaetes to join
            covenants = ManualCovenant.objects.filter(
                workflow=workflow,
                bool_confirmed=True
            )
            for covenant in covenants:
                covenant.join_candidates = gather_all_manual_covenant_candidates(covenant)
            ManualCovenant.objects.bulk_update(covenants, fields=['join_candidates'], batch_size=5000)
