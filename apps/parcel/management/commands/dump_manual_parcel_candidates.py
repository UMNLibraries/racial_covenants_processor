import os
import datetime
import pandas as pd

from django.db.models import F
from django.utils.text import slugify
from django.core.management.base import BaseCommand

from django.conf import settings

from apps.parcel.models import ManualParcelCandidate


class Command(BaseCommand):
    '''Save a CSV of ManualParcelCandidate objects for archiving and later reloading.'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            mpces = ManualParcelCandidate.objects.filter(
                workflow__workflow_name=workflow_name
            ).values()

            mpc_df = pd.DataFrame(mpces)
            mpc_df.rename(columns={'id': 'db_id'}, inplace=True)
            mpc_df.drop(
                columns=['workflow_id', 'parcel_id'], inplace=True, errors='ignore')

            print(mpc_df)
            backup_dir = os.path.join(settings.BASE_DIR, 'data', 'backup')
            os.makedirs(backup_dir, exist_ok=True)

            outfile = os.path.join(backup_dir,
                                   f'manual_parcel_candidates_{slugify(workflow_name)}_{datetime.datetime.now().date()}.csv')
            print(outfile)
            mpc_df.to_csv(outfile, index=False)
