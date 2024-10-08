from django.core import management
from django.core.management.base import BaseCommand

from apps.parcel.models import ManualParcelCandidate


class Command(BaseCommand):
    '''Load a downloaded CSV of ManualParcelCandidate objects into the database and join to Parcels.'''

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

            print("Loading extra parcels...")

            # Make custom mapping from model fields to drop IP column
            mapping = {
                # model: csv
                'parcel_pin_primary': 'parcel_pin_primary',
                'workflow_name': 'workflow_name',
                'addition': 'addition',
                'lot': 'lot',
                'block': 'block',
                'date_added': 'date_added',
                'date_updated': 'date_updated',
                'comments': 'comments',
            }

            insert_count = ManualParcelCandidate.objects.from_csv(
                infile, mapping=mapping)
            print("{} records inserted".format(insert_count))

            management.call_command(
                'connect_manual_parcel_candidates', workflow=workflow_name)
