from django.core import management
from django.core.management.base import BaseCommand

from apps.zoon.models import ManualCorrection


class Command(BaseCommand):
    '''Load a downloaded CSV of ManualCorrection objects into the datbase and join to ZooniverseSubjects.'''

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

        if not infile:
            print('Missing infile path. Please specify with --infile.')
            return False
        else:

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
                'seller': 'seller',
                'buyer': 'buyer',
                'deed_date': 'deed_date',
                'date_added': 'date_added',
                'date_updated': 'date_updated',
                'comments': 'comments',
            }

            insert_count = ManualCorrection.objects.from_csv(
                infile, mapping=mapping)
            print("{} records inserted".format(insert_count))

            # Handle reducer output to develop consensus answers
            management.call_command(
                'connect_manual_corrections', workflow=workflow_name)
