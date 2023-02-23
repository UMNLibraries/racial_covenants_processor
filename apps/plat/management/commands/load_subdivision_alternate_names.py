from django.core import management
from django.core.management.base import BaseCommand

from apps.plat.models import SubdivisionAlternateName


class Command(BaseCommand):
    '''Load a downloaded CSV of SubdivisionAlternateName objects into the database and join to Subdivisions.'''

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

            print("Loading subdivision alternate names...")

            # Make custom mapping from model fields to drop IP column
            mapping = {
                # model: csv
                'zoon_workflow_id': 'zoon_workflow_id',
                'subdivision_name': 'subdivision_name',
                'alternate_name': 'alternate_name',
                'alternate_name_standardized': 'alternate_name_standardized',
            }

            insert_count = SubdivisionAlternateName.objects.from_csv(
                infile, mapping=mapping)
            print("{} records inserted".format(insert_count))

            # Handle reducer output to develop consensus answers
            management.call_command(
                'connect_subdivision_alternate_names', workflow=workflow_name)
