import os
import re
import csv
import json
import uuid
import boto3
import datetime
import pandas as pd
from pathlib import PurePath
from multiprocessing.pool import ThreadPool

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.deed.models import DeedPage
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):

    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    s3 = session.resource('s3')

    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

    sfn_client = boto3.client('stepfunctions')

    done_manifest_path = None

    num_threads = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

        parser.add_argument('-f', '--full', action='store_true',
                            help='Delete old processed records and start over (as opposed to completing a half-done process.)')
        
        parser.add_argument('-p', '--pool', type=int,
                            help='How many threads to use? (Default is 8)')

    def chunk_list(self, input_list, chunk_size):
        for i in range(0, len(input_list), chunk_size):
            yield input_list[i:i + chunk_size]

    def delete_matching_hits(self, workflow):
        delete_confirmation = input(f'WARNING: ABOUT TO DELETE ALL EXISTING HITS JSONS IN WORKFLOW {workflow.slug}... Confirm? [Y/N] ')

        # input validation
        if delete_confirmation.lower() in ('y', 'yes'):

            keys_to_delete = [{'Key': obj.key} for obj in self.bucket.objects.filter(
                Prefix=f'ocr/hits/{workflow.slug}/'
            )]

            print(f'Deleting {len(keys_to_delete)} hit objects ...')
            for chunk in self.chunk_list(keys_to_delete, 1000):
                boto3.client('s3').delete_objects(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Delete={'Objects': chunk}
                )
            return True

        elif delete_confirmation.lower() in ('n', 'no'):
            print('Confirmation declined, stopping process...')
            return False
        else:
            print(f'Error: Input {delete_confirmation} unrecognized.')
            return False

    def build_event(self, key):

        now = datetime.datetime.now().timestamp()

        return {
          "version": "0",
          "id": "17793124-05d4-b198-2fde-7ededc63b103",
          "detail-type": "Deed machine term search update",
          "source": "deedmachine.s3",
          "account": "123456789012",
          "time": now,
          "region": settings.AWS_S3_REGION_NAME,
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

    def check_already_processed(self, workflow_slug, upload_keys):
        print("Checking for manifest to see what images have already been re-processed...")

        try:
            already_triggered_keys = pd.read_csv(self.done_manifest_path, names=['filename']).filename.to_list()

            remaining_to_upload = list(set(upload_keys).symmetric_difference(set(already_triggered_keys)))

            print(
                f"Found {len(already_triggered_keys)} images already uploaded out of {len(upload_keys)}, {len(remaining_to_upload)} remaining...")
        except:
            print("No done manifest file found.")
            remaining_to_upload = upload_keys

        return remaining_to_upload

    def trigger_step_function(self, key):

        response = self.sfn_client.start_execution(
            stateMachineArn=settings.TERMSEARCHUPDATE_STATE_MACHINE,
            name=f'update_term_search_{uuid.uuid4().hex}',
            input=json.dumps(self.build_event(key))
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            with open(self.done_manifest_path, 'a') as done_manifest:
                done_manifest.write(key + '\n')
            return key
        return False

    def trigger_raw_put(self, workflow, full=False):
    
        put_confirmation = input(f'WARNING: ABOUT TO TRIGGER RAW FILE PUTS IN WORKFLOW {workflow.slug}, WHICH WILL INCUR AWS CHARGES... Confirm? [Y/N] ')

        # input validation
        if put_confirmation.lower() in ('y', 'yes'):

            key_filter = re.compile(f"ocr/json/{workflow.slug}/.+\.json")

            print(f'Gathering list of OCRed images in {workflow.slug} workflow ...')

            matching_keys = [obj.key for obj in self.bucket.objects.filter(
                Prefix=f'ocr/json/{workflow.slug}/'
            ) if re.match(key_filter, obj.key)]

            today = datetime.date.today().strftime('%Y%m%d')
            export_dir = os.path.join(settings.BASE_DIR, 'data', 'main_exports')
            os.makedirs(export_dir, exist_ok=True)
            self.done_manifest_path = os.path.join(
                export_dir, f"{workflow.slug}_re-ocr_complete_{today}.csv")

            if not full:
                # Filter out ones that already have been re-processed
                matching_keys = self.check_already_processed(workflow.slug, matching_keys)
                # matching_keys = ['raw/wi-milwaukee-county/19010521/00421264_PLAT_0001.tif']

            print(f'Found {len(matching_keys)} matching images to trigger events on.')

            trigger_count = 0

            pool = ThreadPool(processes=self.num_threads)
            pool.map(self.trigger_step_function, matching_keys)

        else:
            print('Cancelling...')

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        self.num_threads = kwargs['pool'] if kwargs['pool'] else 16

        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            if kwargs['full']:
                delete_successful = self.delete_matching_hits(workflow)
                if not delete_successful:
                    return False

                self.trigger_raw_put(workflow, True)
            else:
                self.trigger_raw_put(workflow)
