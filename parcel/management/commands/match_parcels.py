import re
import os

from django.core.management.base import BaseCommand
from django.conf import settings

from parcel.models import Parcel
from parcel.utils.parcel_utils import get_parcel_options
from zoon.models import ZooniverseWorkflow, ZooniverseSubject
from zoon.utils.zooniverse_config import get_workflow_version


class Command(BaseCommand):
    '''Attempt to auto-join covenants to modern parcels using current values'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def match_parcels_bulk(self, workflow):
        covenant_lots_to_find = []
        for covenant in ZooniverseSubject.objects.filter(
            workflow=workflow,
            bool_covenant_final=True
        ):
            candidates, metadata = get_parcel_options(covenant)
            covenant_lots_to_find += candidates

        # print(covenant_lots_to_find)

        # print(covenant_lots_to_find)
        print(ZooniverseSubject.objects.filter(
            workflow=workflow,
            bool_covenant_final=True
        ).count())
        print("Lots to check", len(covenant_lots_to_find))
        print("Subjects with lots to check", len(
            set([s['subject_id'] for s in covenant_lots_to_find])))

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            # This config info comes from local_settings, generally.
            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            self.batch_dir = os.path.join(
                settings.BASE_DIR, 'data', 'zooniverse_exports', self.batch_config['panoptes_folder'])

            # Get workflow version from config yaml
            workflow_version = get_workflow_version(
                self.batch_dir, self.batch_config['config_yaml'])

            workflow = ZooniverseWorkflow.objects.get(
                workflow_name=workflow_name, version=workflow_version)

            self.match_parcels_bulk(workflow)
