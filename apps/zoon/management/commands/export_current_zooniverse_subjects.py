import os
import datetime
import pandas as pd

import panoptes_client
from panoptes_client import Panoptes, Project, Subject, SubjectSet

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.zoon.utils.zooniverse_load import build_zooniverse_manifest, connect_to_zooniverse, get_subject_set, get_existing_subjects
from apps.deed.models import DeedPage


class Command(BaseCommand):
    '''
    This command exports metadata for DeedPage subjects currently uploaded to Zooniverse.

    To connect to panoptes the zooniverse user_name and password must be stored
    in the users operating system environmental variables USERNAME and PASSWORD.
    If this is not the case line 96 must be modified to the form
    Panoptes.connect(username='jmschell', password='actual-password'), and
    steps must be taken to protect this script.
    NOTE: You may use a file to hold the command-line arguments like:
    @/path/to/args.txt.
    '''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "WI Milwaukee County"')
    
    def save_report_local(self, df, version_slug):
        out_csv = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{version_slug}.csv")
        df.to_csv(out_csv, index=False)

        return out_csv

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']

        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
            return False
        else:
            workflow = get_workflow_obj(workflow_name)

        zooniverse_project = connect_to_zooniverse()
        subject_set = get_subject_set(zooniverse_project, workflow)

        existing_subjects = get_existing_subjects(subject_set)

        print(f"Found {len(existing_subjects)} existing subjects. Building manifest...")

        subjects_df = pd.DataFrame.from_dict(existing_subjects)

        print(subjects_df)

        now = datetime.datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M')
        version_slug = f"{workflow.slug}_uploaded_zoon_subjects_{timestamp}"

        match_report_local = self.save_report_local(subjects_df, version_slug)