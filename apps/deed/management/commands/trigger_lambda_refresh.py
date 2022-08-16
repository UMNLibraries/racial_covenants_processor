# import os
import re
import json
import time
import uuid
import boto3
import datetime
import pandas as pd
from pathlib import PurePath

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

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

        parser.add_argument('-f', '--full', action='store_true',
                            help='Delete old processed records and start over (as opposed to completing a half-done process.)')

    def countdown(self, seconds=5):
        while seconds > 0:
            print(f"{seconds}...")
            time.sleep(1)
            seconds-=1

    def chunk_list(self, input_list, chunk_size):
        for i in range(0, len(input_list), chunk_size):
            yield input_list[i:i + chunk_size]

    def delete_matching_stats(self, workflow):
        print(f"WARNING: ABOUT TO DELETE ALL EXISTING STATS JSONS IN WORKFLOW {workflow.slug}...")

        self.countdown()

        # my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        keys_to_delete = [{'Key': obj.key} for obj in self.bucket.objects.filter(
            Prefix=f'ocr/stats/{workflow.slug}/'
        )]

        print(f'Deleting {len(keys_to_delete)} keys ...')
        for chunk in self.chunk_list(keys_to_delete, 1000):
            boto3.client('s3').delete_objects(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Delete={'Objects': chunk}
            )

    def delete_matching_hits(self, workflow):
        print(f"WARNING: ABOUT TO DELETE ALL EXISTING HITS JSONS IN WORKFLOW {workflow.slug}...")

        self.countdown()

        keys_to_delete = [{'Key': obj.key} for obj in self.bucket.objects.filter(
            Prefix=f'ocr/hits/{workflow.slug}/'
        )]

        print(f'Deleting {len(keys_to_delete)} keys ...')
        for chunk in self.chunk_list(keys_to_delete, 1000):
            boto3.client('s3').delete_objects(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Delete={'Objects': chunk}
            )

    def build_event(self, key):

        now = datetime.datetime.now().timestamp()

        return {
          "version": "0",
          "id": "17793124-05d4-b198-2fde-7ededc63b103",
          "detail-type": "Mapping Prejudice deed machine fake OCR",
          "source": "mappingprejudice.s3",
          "account": "123456789012",
          "time": now,
          "region": "us-east-2",
          "resources": ["arn:aws:s3:::covenants-deed-images"],
          "detail": {
            "version": "0",
            "bucket": {
              "name": "covenants-deed-images"
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
        print("Checking s3 to see what images have already been re-processed...")
        # s3 = self.session.resource('s3')
        # my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        key_filter = re.compile(f"ocr/stats/{workflow_slug}/.+\.json")

        existing_keys = [obj.key for obj in self.bucket.objects.filter(
            Prefix=f'ocr/stats/{workflow_slug}/'
        ) if re.match(key_filter, obj.key)]

        stat_keys_to_check = [re.sub(r'__[a-z0-9]+\.json', r'.tif', key.replace('ocr/stats/', 'raw/')) for key in existing_keys]

        print(stat_keys_to_check)

        # subtract already uploaded matching_keys from web_keys_to_check
        already_uploaded = set(stat_keys_to_check).intersection(upload_keys)
        remaining_to_upload = [
            u for u in upload_keys if u not in already_uploaded]
        print(
            f"Found {len(already_uploaded)} images already uploaded out of {len(upload_keys)}, {len(remaining_to_upload)} remaining...")

        return remaining_to_upload

    def trigger_raw_put(self, workflow):
        print("WARNING: ABOUT TO TRIGGER RAW FILE PUTS, WHICH MAY INCUR LARGE AWS CHARGES...")

        self.countdown()

        # Then use the session to get the resource
        # s3 = self.session.resource('s3')
        # my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        key_filter = re.compile(f"raw/{workflow.slug}/.+\.tif")

        print(f'Gathering list of raw images in {workflow.slug} workflow ...')

        matching_keys = [obj.key for obj in self.bucket.objects.filter(
            Prefix=f'raw/{workflow.slug}/'
        ) if re.match(key_filter, obj.key)]

        # Filter out ones that already have been re-processed
        matching_keys = self.check_already_processed(workflow.slug, matching_keys)
        # matching_keys = ['raw/wi-milwaukee-county/19010521/00421264_PLAT_0001.tif']

        print(f'Found {len(matching_keys)} matching images to trigger events on.')

        sfn_client = boto3.client('stepfunctions')

        for mk in matching_keys:

            response = sfn_client.start_execution(
                stateMachineArn=settings.REPROCESSING_STATE_MACHINE,
                name=f'fake_ocr_{uuid.uuid4().hex}',
                input=json.dumps(self.build_event(mk))
            )
            print(response)


    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            if kwargs['full']:
                # TODO: add confirmation requirement
                self.delete_matching_stats(workflow)
                self.delete_matching_hits(workflow)

            self.trigger_raw_put(workflow)
