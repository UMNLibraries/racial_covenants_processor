import os
import json
import datetime
import pandas as pd
from sqlalchemy import create_engine

from django.core.management.base import BaseCommand
from django.db.models import F
from django.conf import settings

from apps.zoon.models import ZooniverseSubject, ReducedResponse_Question, ReducedResponse_Text


class Command(BaseCommand):
    '''This is the main loader for a Zooniverse export and set of reduced output into the Django app.'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str, help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            subjects = ZooniverseSubject.objects.filter(
                workflow__workflow_name=workflow_name
            ).annotate(
                workflow_name=F('workflow__workflow_name')
            ).values()

            subjects_df = pd.DataFrame(subjects)
            subjects_df.rename(columns={'id': 'db_id'}, inplace=True)
            subjects_df.drop(columns=['workflow_id'], inplace=True)

            print(subjects_df)

            outfile = os.path.join(settings.BASE_DIR, 'data', 'analysis', f'ramsey_subjects_merged_zooniverse_{datetime.datetime.now().date()}.csv')
            print(outfile)
            subjects_df.to_csv(outfile, index=False)
