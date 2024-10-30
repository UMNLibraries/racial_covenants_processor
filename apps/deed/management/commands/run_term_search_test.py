import os
import csv
import json
import boto3
import datetime
from multiprocessing.pool import ThreadPool

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.deed.models import DeedPage
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    """ This command is used to test fuzzy search terms currently in use against a random sample of N OCR JSONS, and export a csv with pointers to the resulting files for easier checking"""

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    s3 = session.client('s3')
    lambda_client = boto3.client('lambda')

    term_test_result_path = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

        parser.add_argument('-n', '--num_results', type=int,
                            help='Against how many pages do you want the test to run (Default is 100)?')

        parser.add_argument('-ho', '--hits_only', action='store_true',
                            help='Only test DeedPages that have been flagged as conventional hits.')

    def get_test_deedpages(self, workflow=None, n=100, bool_hits_only=False):
        """Get a random sample of n (default 100) existing OCR JSON objects generated by Textract in the preliminary stages of the Deed Machine. Manually excluding legacy Ramsey County workflow, which does not include OCR text and thus can't be tested."""

        print(f'Gathering list of {n} OCRed images ...')

        kwargs = {}
        if workflow:
            kwargs['workflow'] = workflow
        
        if bool_hits_only:
            kwargs['bool_match'] = True

        out_values = ['workflow__slug', 's3_lookup', 'page_ocr_json', 'page_ocr_text', 'page_image_web', 'page_stats', 'public_uuid', 'bool_match']

        if len(kwargs) > 0:
            random_deedpages = DeedPage.objects.filter(**kwargs).exclude(workflow__workflow_name="Ramsey County").order_by('?').values(*out_values)[:n]
        else:
            random_deedpages = DeedPage.objects.exclude(workflow__workflow_name="Ramsey County").order_by('?').values(*out_values)[:n]

        return random_deedpages
    
    def process_lambda_response(self, deedpage_obj, response):
        response_payload = json.loads(response['Payload'].read().decode('utf-8').replace("'", '"'))

        if response['ResponseMetadata']['HTTPStatusCode'] in [200, 202]:
            try:
                test_status = 'Complete'
                bool_fuzzy_match = str(response_payload['body']['bool_hit'])
                fuzzy_match_json = str(response_payload['body']['match_file'])
            except KeyError:
                test_status = 'No result'
                bool_fuzzy_match = ''
                fuzzy_match_json = ''
        else:
            print(response['Payload'].read())

            test_status = 'Error'
            bool_fuzzy_match = ''
            fuzzy_match_json = ''

        out_csv_dict = {
            'workflow': deedpage_obj['workflow__slug'],
            's3_lookup': deedpage_obj['s3_lookup'],
            'page_ocr_text': deedpage_obj['page_ocr_text'],
            'bool_basic_match': str(deedpage_obj['bool_match']),
            'bool_fuzzy_match': bool_fuzzy_match,
            'fuzzy_match_json': fuzzy_match_json,
            'test_status': test_status,
            'match_context': ''
        }

        return out_csv_dict

    def load_s3_json(self, key):
        try:
            content_object = self.s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
            json_obj = json.loads(content_object['Body'].read().decode('utf-8').replace("'", '"'))
            return json_obj
        except json.decoder.JSONDecodeError:
            return None
    
    def read_match_file(self, fuzzy_match_json_key):
        match_json = self.load_s3_json(fuzzy_match_json_key)
        if match_json:

            found_terms = [{'term': k, 'line_nums': v} for k, v in match_json.items() if k not in ['workflow', 'lookup', 'uuid']]

            return found_terms
        return False

    def extract_match_context(self, match_details, ocr_json):
        ocr_lines = [block for block in ocr_json['Blocks'] if block['BlockType'] == 'LINE']

        print(match_details)

        out_context = []
        for term in match_details:
            line_texts = []
            # Add text of each line containing a match
            for line in term['line_nums']:
                print(ocr_lines[line]['Text'])
                line_texts.append(ocr_lines[line]['Text'])
            out_context.append({'term': term['term'], 'line_nums': term['line_nums'], 'lines': line_texts})
        return out_context
            
    def trigger_lambda(self, deedpage_obj):

        payload = {
            "statusCode": 200,
            "body": {
                "message": "Term search test",
                "bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "orig": 'Test key',
                "json": deedpage_obj['page_ocr_json'],
                "txt": deedpage_obj['page_ocr_text'],
                "stats": deedpage_obj['page_stats'],
                "uuid": deedpage_obj['public_uuid'],
                "handwriting_pct": '0'
            },
        }

        print(f"Triggering Lambda on {deedpage_obj['workflow__slug']} {deedpage_obj['s3_lookup']}...")

        response = self.lambda_client.invoke(
            FunctionName=settings.TERMSEARCHTEST_LAMBDA,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload),
        )

        test_response = self.process_lambda_response(deedpage_obj, response)

        if test_response['fuzzy_match_json'] not in ['', 'None', None]:
            match_details = self.read_match_file(test_response['fuzzy_match_json'])

            # ocr_json = self.load_s3_json(deedpage_obj['page_ocr_json'])
            ocr_json_file = self.s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=deedpage_obj['page_ocr_json'])
            
            try:
                ocr_json = json.loads(ocr_json_file['Body'].read().decode('utf-8'))
            except json.decoder.JSONDecodeError:
                print(ocr_json_file['Body'].read().decode('utf-8'))

            if ocr_json:
                match_context = self.extract_match_context(match_details, ocr_json)
                test_response['match_context'] = '"' + json.dumps(match_context).replace('"', "'") + '"'

        with open(self.term_test_result_path, 'a') as done_manifest:
            writer = csv.writer(done_manifest)
            writer.writerow(test_response.values())

        return test_response['test_status']

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if workflow_name:
            workflow = get_workflow_obj(workflow_name)
            workflow_slug = workflow.slug
        else:
            print('Workflow not specified. Running test on against random selection across workflows. (To test against a specific workflow, please specify with --workflow.)')
            workflow = None
            workflow_slug = 'all_workflows'
            
        num_results = kwargs['num_results']
        if not num_results:
            num_results = 100

        bool_hits_only = kwargs['hits_only']
        hit_str = ''
        if bool_hits_only:
            hit_str = '_hits_only'

        now = datetime.datetime.now().strftime('%Y%m%d_%H%M')

        self.term_test_result_path = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{workflow_slug}_fuzzy_term_search_test{hit_str}_{now}.csv")
        
        with open(self.term_test_result_path, 'w') as done_manifest:
            done_manifest.write("workflow,s3_lookup,page_ocr_text,bool_basic_match,bool_fuzzy_match,fuzzy_match_json,test_status,match_context\n")

        # Get random set of DeedPage objects to test against
        random_deedpages = self.get_test_deedpages(workflow, num_results, bool_hits_only)

        # Trigger fuzzy term search update for each test page
        pool = ThreadPool(processes=12)
        pool.map(self.trigger_lambda, random_deedpages)
