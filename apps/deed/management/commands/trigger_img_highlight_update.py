import os
import csv
import json
import boto3
import datetime
from multiprocessing.pool import ThreadPool

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.conf import settings

from apps.deed.models import DeedPage
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    """ This command is used to test fuzzy search terms currently in use against a random sample of N OCR JSONS, and export a csv with pointers to the resulting files for easier checking"""

    try:
        profile_name = settings.AWS_PROFILE
    except:
        profile_name = 'default'

    try:
        region_name = settings.AWS_REGION_NAME
    except:
        region_name = 'us-east-2'

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
             profile_name=profile_name,
             region_name=region_name)

    s3 = session.resource('s3')

    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

    s3_client = session.client('s3')
    lambda_client = session.client('lambda')
    term_test_result_path = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        
        parser.add_argument('-t', '--term', type=str,
                            help='Only reprocess DeedPage objects which previously matched a specific term.')


    def get_existing_deedpages(self, workflow):
        """Get DeedPage results to clear and overwrite. By default, only hits, but can be set to get all in workflow"""

        if not workflow:
            print("Workflow variable required.")
            raise
        
        out_values = ['workflow__slug', 's3_lookup', 'page_ocr_json', 'page_ocr_text', 'page_image_web', 'page_stats', 'public_uuid', 'bool_match']

        dps = DeedPage.objects.filter(workflow=workflow).filter(Q(bool_match=True) | Q(bool_exception=True)).values(*out_values)

        return dps
    
    
    def process_lambda_response(self, deedpage_obj, response):
        response_payload = json.loads(response['Payload'].read().decode('utf-8'))
        print(response_payload)

        if response['ResponseMetadata']['HTTPStatusCode'] in [200, 202]:
            try:
                test_status = 'Complete'
                highlighted_img = str(response_payload['body']['highlighted_img'])
            except KeyError:
                test_status = 'No result'
                highlighted_img = ''
        else:
            print(response['Payload'].read())

            test_status = 'Error'
            highlighted_img = ''

        out_csv_dict = {
            'workflow': deedpage_obj['workflow__slug'],
            's3_lookup': deedpage_obj['s3_lookup'],
            'page_ocr_text': deedpage_obj['page_ocr_text'],
            'bool_basic_match': str(deedpage_obj['bool_match']),
            'highlighted_img': highlighted_img,
            'test_status': test_status,
            'match_context': ''
        }

        return out_csv_dict

            
    def trigger_lambda(self, deedpage_obj, fuzzy=True):

        if fuzzy:
            match_dir = 'ocr/hits_fuzzy/'
        else:
            match_dir = 'ocr/hits/'

        payload = {
            "statusCode": 200,
            "body": {
                "message": "Image highlight update",
                "bool_hit": True,
                "bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "orig_img": 'Test key',
                "ocr_json": deedpage_obj['page_ocr_json'],
                "match_file": deedpage_obj['page_ocr_json'].replace('ocr/json/', 'ocr/hits_fuzzy/'),
                "web_img": deedpage_obj['page_image_web'],
                "uuid": deedpage_obj['public_uuid'],
                "handwriting_pct": '0'
            },
        }

        print(f"Triggering Lambda on {deedpage_obj['workflow__slug']} {deedpage_obj['s3_lookup']}...")

        response = self.lambda_client.invoke(
            FunctionName=settings.IMGHIGHLIGHT_LAMBDA,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload),
        )

        test_response = self.process_lambda_response(deedpage_obj, response)

        return test_response['test_status']

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if workflow_name:
            workflow = get_workflow_obj(workflow_name)
            workflow_slug = workflow.slug
        else:
            print('Workflow not specified.')
            workflow = None
            return False

        dps = self.get_existing_deedpages(workflow)

        # Trigger fuzzy term search update for each test page
        pool = ThreadPool(processes=12)
        pool.map(self.trigger_lambda, dps)
