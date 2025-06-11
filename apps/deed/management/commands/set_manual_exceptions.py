import os
import datetime
import pandas as pd

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.conf import settings

from apps.deed.models import DeedPage
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Using a CSV, set certain DeedPage results as exemptions even if they have been flagged as matches.

    'Sample Workflow': {
        'deed_manual_exceptions': [
            {
                'data_csv': os.path.join(settings.BASE_DIR, '../apps/deed/fixtures/manual_exceptions_test_data.csv'),
                'join_field_deed': 's3_lookup',
                'join_field_csv': 's3_lookup',
            }
        ]
    }
    '''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        
        parser.add_argument('-f', '--infile', type=str,
                            help='Path to CSV file of dumped corrections. Otherwise will use settings in workflow settings under ')
        
        parser.add_argument('-c', '--column', type=str, default='s3_lookup',
                            help='Column name to use to join to DeedPage records. Must match a DeedPage column that is also in the CSV. Defaults to s3_lookup')
        
    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        infile = kwargs['infile']
        column = kwargs['column']

        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

        if infile:
            exception_files = [
                {'data_csv': infile, 'field': column}
            ]
        else:
            # Get CSV and field names from settings object
            if 'deed_manual_exceptions' in settings.ZOONIVERSE_QUESTION_LOOKUP[workflow.workflow_name]:
                exception_files = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow.workflow_name]['deed_manual_exceptions']

        for exception_file in exception_files:
            print(f"Attempting to exempt DeedPage objets in {exception_file['data_csv']} by joining on column {exception_file['field']}...")
            df = pd.read_csv(exception_file['data_csv'])

            lookup_vals = df[exception_file['field']].to_list()

            pages_to_update = []
            filter_kwargs = {
                'workflow': workflow,
                'bool_match': True,
                f'{exception_file['field']}__in': lookup_vals
            }
            print('Retrieving DeedPage records...')
            for dp in DeedPage.objects.filter(**filter_kwargs).only('pk'):
                dp.bool_match = False
                dp.bool_exception = True
                dp.bool_manual = True
                pages_to_update.append(dp)

            print(f'Setting {len(pages_to_update)} pages as manual exceptions ...')
            DeedPage.objects.bulk_update(
                pages_to_update, ['bool_match', 'bool_exception', 'bool_manual'])
