import pandas as pd

from django.core import management
from django.core.management.base import BaseCommand

from apps.zoon.models import ManualCorrection
from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.zoon.utils.django_export import check_workflow_match


class Command(BaseCommand):
    '''Load a downloaded CSV of ManualCorrection objects into the database and join to ZooniverseSubjects.'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

        parser.add_argument('-f', '--infile', type=str,
                            help='Path to CSV file of dumped corrections')

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

            print("Loading manual corrections...")

            # Make custom mapping from model fields to drop IP column
            mapping = {
                # model: csv
                'zoon_subject_id': 'zoon_subject_id',
                'zoon_workflow_id': 'zoon_workflow_id',
                'bool_covenant': 'bool_covenant',
                'covenant_text': 'covenant_text',
                'addition': 'addition',
                'lot': 'lot',
                'block': 'block',
                'map_book': 'map_book',
                'map_book_page': 'map_book_page',
                'seller': 'seller',
                'buyer': 'buyer',
                'deed_date': 'deed_date',
                'date_added': 'date_added',
                'date_updated': 'date_updated',
                'match_type': 'match_type',
                'comments': 'comments',
            }

            insert_count = ManualCorrection.objects.from_csv(
                infile, mapping=mapping)
            print("{} records inserted".format(insert_count))

            management.call_command(
                'connect_manual_corrections', workflow=workflow_name)
