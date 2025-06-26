import pandas as pd

from django.core import management
from django.core.management.base import BaseCommand

from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.zoon.utils.django_export import check_workflow_match
from apps.zoon.models import ZooniverseResponseProcessed


class Command(BaseCommand):
    '''Load a downloaded CSV of ZooniverseResponseProcessed objects into the database, either to migrate to a different workflow or restore backup info.'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to load responses into, e.g. "MN Ramsey County"')

        parser.add_argument('-f', '--infile', type=str,
                            help='Path to CSV file of dumped responses')
        
    def handle(self, *args, **kwargs):

        workflow_name = kwargs['workflow']
        infile = kwargs['infile']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
            return False
        else:
            workflow = get_workflow_obj(workflow_name)

        if not infile:
            print('Missing infile path. Please specify with --infile.')
            return False
        else:

            bool_workflow_match = check_workflow_match(workflow, infile)
            if not bool_workflow_match:
                return False

            print(f"Loading ZooniverseResponseProcessed objects into workflow {workflow_name}...")

            mapping = {
                # model: csv
                # 'id': 'db_id',
                'classification_id': 'classification_id',
                'user_name': 'user_name',
                'user_id': 'user_id',
                'bool_covenant': 'bool_covenant',
                'covenant_text': 'covenant_text',
                'addition': 'addition',
                'lot': 'lot',
                'block': 'block',
                'map_book': 'map_book',
                'map_book_page': 'map_book_page',
                'city': 'city',
                'seller': 'seller',
                'buyer': 'buyer',
                'match_type': 'match_type',
                'bool_handwritten': 'bool_handwritten',
                'deed_date_year': 'deed_date_year',
                'deed_date_month': 'deed_date_month',
                'deed_date_day': 'deed_date_day',
                'created_at': 'created_at',
                # 'workflow_name': 'workflow_name',
                'zoon_subject_id': 'zoon_subject_id',
                # 'zoon_workflow_id': 'zoon_workflow_id',
            }

            insert_count = ZooniverseResponseProcessed.objects.from_csv(
                infile,
                mapping=mapping,
                force_not_null=['covenant_text', 'deed_date_year', 'deed_date_month', 'deed_date_day'],
                static_mapping={
                    "workflow_id": workflow.id
                }
            )
            print("{} records inserted".format(insert_count))

            management.call_command(
                'connect_django_individual_responses', workflow=workflow_name)
