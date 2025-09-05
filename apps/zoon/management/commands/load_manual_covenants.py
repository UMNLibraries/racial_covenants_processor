import datetime
from django.core import management
from django.core.management.base import BaseCommand

from apps.zoon.models import ManualCovenant

from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.zoon.utils.django_export import check_workflow_match


class Command(BaseCommand):
    '''Load a downloaded CSV of ManualCovenant objects into the database.'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

        parser.add_argument('-f', '--infile', type=str,
                            help='Path to CSV file of manual covenants')

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

            print("Loading manual covenants from CSV...")

            # Make custom mapping from model fields to drop IP column
            mapping = {col: col for col in [
                'bool_confirmed',
                'covenant_text',
                'addition',
                'lot',
                'block',
                'map_book',
                'map_book_page',
                'seller',
                'buyer',
                'deed_date',
                'doc_num',
                'city',
                'cov_type',
                'comments',
                'join_candidates',
                'bool_parcel_match',
                'date_added',
                'date_updated',
            ]}

            static_mapping = {
                'workflow_id': workflow.id,
                # 'cov_type': 'PS',
                # 'bool_confirmed': True,
                # 'bool_parcel_match': False,
                # 'date_added': datetime.datetime.now(),
                # 'date_updated': datetime.datetime.now(),
            }

            insert_count = ManualCovenant.objects.from_csv(
                infile,
                mapping=mapping,
                static_mapping=static_mapping,
                force_not_null=['doc_num', 'addition', 'lot', 'block', 'map_book', 'map_book_page', 'covenant_text', 'city', 'seller', 'buyer'],
            )
            print("{} records inserted".format(insert_count))
