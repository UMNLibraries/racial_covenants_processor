import os
import datetime
import pandas as pd

from django.db.models import F
from django.utils.text import slugify
from django.core.management.base import BaseCommand

from django.conf import settings

from apps.zoon.models import ExtraParcelCandidate


class Command(BaseCommand):
    '''Save a CSV of ExtraParcelCandidate objects for archiving and later reloading.'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            epces = ExtraParcelCandidate.objects.filter(
                workflow__workflow_name=workflow_name
            ).annotate(
                workflow_name=F('workflow__workflow_name')
            ).values()

            epc_df = pd.DataFrame(epces)
            epc_df.rename(columns={'id': 'db_id'}, inplace=True)
            epc_df.drop(
                columns=['workflow_id', 'zooniverse_subject_id'], inplace=True)

            print(epc_df)
            backup_dir = os.path.join(settings.BASE_DIR, 'data', 'backup')
            os.makedirs(backup_dir, exist_ok=True)

            outfile = os.path.join(backup_dir,
                                   f'extra_parcels_{slugify(workflow_name)}_{datetime.datetime.now().date()}.csv')
            print(outfile)
            epc_df.to_csv(outfile, index=False)
