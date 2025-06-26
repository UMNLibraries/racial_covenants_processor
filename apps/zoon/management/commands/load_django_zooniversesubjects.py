import pandas as pd

from django.core import management
from django.core.management.base import BaseCommand

from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.zoon.utils.django_export import check_workflow_match
from apps.zoon.models import ZooniverseSubject


class Command(BaseCommand):
    '''Load a downloaded CSV of ZooniverseSubject objects into the database, either to migrate to a different workflow or restore backup info.'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to load subjectsinto, e.g. "MN Ramsey County"')

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

            print(f"Loading Zooniverse Subjects into workflow {workflow_name}...")

            mapping = {
                # model: csv
                # 'id': 'db_id',
                'zoon_subject_id': 'zoon_subject_id',
                'image_ids': 'image_ids',
                'image_links': 'image_links',
                'dt_retired': 'dt_retired',
                'bool_covenant': 'bool_covenant',
                'bool_problem': 'bool_problem',
                'covenant_text': 'covenant_text',
                'addition': 'addition',
                'lot': 'lot',
                'block': 'block',
                'map_book': 'map_book',
                'map_book_page': 'map_book_page',
                'city': 'city',
                'seller': 'seller',
                'buyer': 'buyer',
                'deed_date': 'deed_date',
                'match_type': 'match_type',
                'bool_handwritten': 'bool_handwritten',
                'deedpage_pk': 'deedpage_pk',
                'deedpage_doc_num': 'deedpage_doc_num',
                'deedpage_s3_lookup': 'deedpage_s3_lookup',
                'bool_covenant_score': 'bool_covenant_score',
                'bool_handwritten_score': 'bool_handwritten_score',
                'match_type_score': 'match_type_score',
                'covenant_text_score': 'covenant_text_score',
                'addition_score': 'addition_score',
                'lot_score': 'lot_score',
                'block_score': 'block_score',
                'map_book_score': 'map_book_score',
                'map_book_page_score': 'map_book_page_score',
                'city_score': 'city_score',
                'seller_score': 'seller_score',
                'buyer_score': 'buyer_score',
                'deed_date_overall_score': 'deed_date_overall_score',
                'deed_date_year_score': 'deed_date_year_score',
                'deed_date_month_score': 'deed_date_month_score',
                'deed_date_day_score': 'deed_date_day_score',
                'median_score': 'median_score',
                'bool_manual_correction': 'bool_manual_correction',
                'bool_covenant_final': 'bool_covenant_final',
                'covenant_text_final': 'covenant_text_final',
                'addition_final': 'addition_final',
                'lot_final': 'lot_final',
                'block_final': 'block_final',
                'map_book_final': 'map_book_final',
                'map_book_page_final': 'map_book_page_final',
                'seller_final': 'seller_final',
                'buyer_final': 'buyer_final',
                'deed_date_final': 'deed_date_final',
                'street_address_final': 'street_address_final',
                'city_final': 'city_final',
                'match_type_final': 'match_type_final',
                'bool_handwritten_final': 'bool_handwritten_final',
                'bool_parcel_match': 'bool_parcel_match',
                'join_candidates': 'join_candidates',
                'parcel_addresses': 'parcel_addresses',
                'parcel_city': 'parcel_city',
                # 'geom_union_4326': 'geom_union_4326',
                'date_updated': 'date_updated',
                # 'workflow_name': 'workflow_name',
            }

            insert_count = ZooniverseSubject.objects.from_csv(
                infile,
                mapping=mapping,
                force_not_null=['addition', 'lot', 'block', 'map_book', 'map_book_page', 'covenant_text', 'city', 'seller', 'buyer'],
                static_mapping={"workflow_id": workflow.id},  # Attempting to overwrite workflow id
            )
            print("{} records inserted".format(insert_count))
