import re
import json
import time
import uuid
import boto3
import datetime
import pandas as pd
from multiprocessing.pool import ThreadPool

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Triggers main step function without upload, using a CSV manifest or scanning of OCR bucket. Useful for cases when images are located in different S3 bucket than final target.'''

    session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    s3 = session.resource('s3')
    sfn_client = boto3.client('stepfunctions')

    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
    in_bucket = None  # Optional if not in same bucket

    min_thread_time = 0
    workflow = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

        parser.add_argument('-m', '--mintime', type=float,
            help='What is the minimum time to execute each thread (rate limit) in seconds (Default is 0)')
        
        parser.add_argument('-p', '--pool', type=int, default=12,
            help='Number of threads. Default = 12')
        
        parser.add_argument('-i', '--infile', type=str,
            help='Path to CSV file of manual covenants')
        
        parser.add_argument('-b', '--inbucket', type=str,
            help='Different starting bucket (optional)')
        
        parser.add_argument('-f', '--full', action='store_true',
            help='Ignore previously processed files. Otherwise, will skip images with matching OCR jsons already existing on S3')
        
    def remove_extra_key_phrases(self, key, workflow_slug):
        out_key = key.replace(
            f'ocr/json/{workflow_slug}/', ''
        ).replace(
            '.json', ''
        ).replace(
            '__MODIFIED', ''
        )

        return re.sub(r'__SPLITPAGE_\d+', '', out_key)
        
    def check_already_uploaded(self, workflow, upload_df):
        print("Checking s3 to see what images have already been uploaded...")
        s3 = self.session.resource('s3')

        # Check for successful OCR json
        key_filter = re.compile(fr"ocr/json/{workflow.slug}/.+\.json")

        matching_keys = [self.remove_extra_key_phrases(obj.key, workflow.slug) for obj in self.bucket.objects.filter(
            Prefix=f'ocr/json/{workflow.slug}/'
        ) if re.match(key_filter, obj.key)]

        print(f"Found {len(matching_keys)} existing OCR JSON keys on S3 that seem to have been successfully processed.")

        # Remove file extension from CSV remainder for comparison to uploaded S3 key
        upload_df['compare_key'] = upload_df.apply(lambda row: row['remainder'].replace(row['extension'], ''), axis=1)
        upload_df = upload_df.merge(
            pd.DataFrame(matching_keys, columns=['compare_key_uploaded']),
            how='left',
            left_on='compare_key',
            right_on='compare_key_uploaded',
            indicator=True
        )
        # Filter out CSV rows with matches from destination s3 bucket
        upload_df = upload_df[upload_df['_merge'] == 'left_only']
        print(f"After filtering, {upload_df.shape[0]} csv rows will be uploaded...")

        return upload_df

    def build_event(self, key):

        now = datetime.datetime.now().timestamp()

        event = {
          "version": "0",
          "id": "17793124-05d4-b198-2fde-7ededc63b103",
          "detail-type": "Mapping Prejudice deed machine main processor",
          "source": "deedmachine.s3",
          "account": "123456789012",
          "time": now,
          "region": "us-east-2",
          "resources": [f"arn:aws:s3:::{settings.AWS_STORAGE_BUCKET_NAME}"],
          "detail": {
            "version": "0",
            "bucket": {
              "name": settings.AWS_STORAGE_BUCKET_NAME
            },
            "object": {
              "key": key,
              "size": 5,
              "etag": "b1946ac92492d2347c6235b4d2611184",
              "version-id": "IYV3p45BT0ac8hjHg1houSdS1a.Mro8e",
              "sequencer": "00617F08299329D189"
            },
            "request-id": "N4N7GDK58NMKJ12R",
            "requester": "123456789012",
            "source-ip-address": "1.2.3.4",
            "reason": "PutObject"
          }
        }

        if self.in_bucket:
            event['detail']['object']['in_bucket'] = self.in_bucket
            event['detail']['object']['out_bucket'] = settings.AWS_STORAGE_BUCKET_NAME

        return event

    def trigger_step_function(self, key):

        start_time = time.time()

        response = self.sfn_client.start_execution(
            stateMachineArn=settings.MAIN_STATE_MACHINE,
            name=f'main_processor_{uuid.uuid4().hex}',
            input=json.dumps(self.build_event(key))
        )
        print(response)

        # If necessary, wait before completing
        if self.min_thread_time > 0:
            elapsed = time.time() - start_time
            time_remaining = self.min_thread_time - elapsed
            if time_remaining > 0:
                print(f'Pausing {time_remaining} seconds')
                time.sleep(time_remaining)

    def get_confirmation(self):
        response = input("Proceed with upload? This may incur large AWS charges. (Y or N)")
        if response.lower() in ['y', 'yes']:
            return True
        return False

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        infile = kwargs['infile']
        bool_full = kwargs['full']

        if kwargs['mintime']:
            self.min_thread_time = kwargs['mintime']

        if kwargs['inbucket']:
            self.in_bucket = kwargs['inbucket']

        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            self.workflow = get_workflow_obj(workflow_name)

        if not infile:
            print('Missing infile path. Please specify with --infile.')
            return False
        else:
            upload_df = pd.read_csv(infile)
            # upload_df = upload_df.head()
            # upload_df = upload_df[upload_df['extension'] == '.pdf'].sample(n=200)
            print(upload_df)

            print(f"Found {upload_df.shape[0]} rows in CSV for potential upload.")

            # Filter out already-processed keys
            if not bool_full:
                filtered_upload_df = self.check_already_uploaded(self.workflow, upload_df)
            else:
                filtered_upload_df = upload_df
                print(f"Uploading all rows because --full selected.")

            raw_images = filtered_upload_df.s3_key.to_list()

            if len(raw_images) == 0:
                print("No rows left to upload.")
                return False
            else:
                confirmed = self.get_confirmation()
                if confirmed:

                    pool = ThreadPool(processes=kwargs['pool'])
                    pool.map(self.trigger_step_function, raw_images)
                
                else:
                    return False
