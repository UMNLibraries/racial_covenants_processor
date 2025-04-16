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
        
        parser.add_argument('-f', '--full', action='store_true',
                    help='Test all DeedPages in workflow, not just previous hits.')

    def get_existing_deedpages(self, workflow, bool_full=False):
        """Get DeedPage results to get word counts for"""

        if not workflow:
            print("Workflow variable required.")
            raise
    
        out_values = ['workflow__slug', 's3_lookup', 'page_image_web', 'page_stats', 'public_uuid', 'bool_match']

        if bool_full:
            dps = DeedPage.objects.filter(workflow=workflow).values(*out_values)
        else:
            dps = DeedPage.objects.filter(
                workflow=workflow,
                bool_match=True
            ).values(*out_values)

        return dps
            
    def get_stats(self, deedpage_obj):

        stats_file = self.s3_client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=deedpage_obj['page_stats'])
            
        try:
            stats_json = json.loads(stats_file['Body'].read().decode('utf-8'))
        except json.decoder.JSONDecodeError:
            print(stats_file['Body'].read().decode('utf-8'))
            stats_json = None

        # {"workflow": "mn-anoka-county", "remainder": "9/30641896", "public_uuid": "3fd32f9072e24cd9876ceea6631b6472", "num_lines": 120, "num_chars": 3637, "handwriting_pct": 0.26}
        if stats_json:
            stats_json['page_image_web'] = deedpage_obj['page_image_web']
            stats_json['bool_match'] = deedpage_obj['bool_match']


            with open(self.term_test_result_path, 'a') as done_manifest:
                writer = csv.writer(done_manifest)
                writer.writerow(stats_json.values())

        return stats_json

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if workflow_name:
            workflow = get_workflow_obj(workflow_name)
            workflow_slug = workflow.slug
        else:
            print('Workflow not specified.')
            workflow = None
            return False
        
        bool_full = kwargs['full']

        dps = self.get_existing_deedpages(workflow, bool_full)

        now = datetime.datetime.now().strftime('%Y%m%d_%H%M')

        self.term_test_result_path = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{workflow_slug}_doc_word_counts_{now}.csv")
        
        with open(self.term_test_result_path, 'w') as done_manifest:
            done_manifest.write("workflow,s3_lookup,public_uuid,num_lines,num_chars,handwriting_pct,page_img_web,bool_match\n")

        # Trigger fuzzy term search update for each test page
        pool = ThreadPool(processes=24)
        pool.map(self.get_stats, dps)
