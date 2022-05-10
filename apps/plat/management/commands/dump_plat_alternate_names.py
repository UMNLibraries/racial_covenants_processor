import os
import datetime
import pandas as pd

from django.db.models import F
from django.utils.text import slugify
from django.core.management.base import BaseCommand

from django.conf import settings

from apps.plat.models import PlatAlternateName


class Command(BaseCommand):
    '''Save a CSV of PlatAlternateName objects for archiving and later reloading.'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            pans = PlatAlternateName.objects.filter(
                workflow__workflow_name=workflow_name
            ).annotate(
                workflow_name=F('workflow__workflow_name')
            ).values()

            pan_df = pd.DataFrame(pans)
            pan_df.rename(columns={'id': 'db_id'}, inplace=True)
            pan_df.drop(
                columns=['workflow_id', 'plat_id'], inplace=True)

            print(pan_df)
            backup_dir = os.path.join(settings.BASE_DIR, 'data', 'backup')
            os.makedirs(backup_dir, exist_ok=True)

            outfile = os.path.join(backup_dir,
                                   f'plat_alternate_names_{slugify(workflow_name)}_{datetime.datetime.now().date()}.csv')
            print(outfile)
            pan_df.to_csv(outfile, index=False)
