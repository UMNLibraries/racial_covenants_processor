from django.core import management
from django.core.management.base import BaseCommand

from apps.zoon.models import ManualParcelPINLink


class Command(BaseCommand):
    '''Load a downloaded CSV of ManualParcelPINLink objects into the database and join to ZooniverseSubjects.'''

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
                'zoon_subject_id': 'zoon_subject_id',
                'zoon_workflow_id': 'zoon_workflow_id',
                'parcel_pin': 'parcel_pin',
                'date_added': 'date_added',
                'date_updated': 'date_updated',
                'comments': 'comments',
            }

            insert_count = ManualParcelPINLink.objects.from_csv(
                infile, mapping=mapping)
            print("{} records inserted".format(insert_count))

            management.call_command(
                'connect_manual_pin_links', workflow=workflow_name)
