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
    '''Attempt to re-OCR records that for some reason got uploaded but didn't make it through to the OCR stage.'''

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
             aws_session_token=getattr(settings, "AWS_SESSION_TOKEN", None))

    s3 = session.resource('s3')

    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

    min_thread_time = 0

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

        parser.add_argument('-m', '--mintime', type=float,
                            help='What is the minimum time to execute each thread (rate limit) in seconds (Default is 0)')

    def countdown(self, seconds=5):
        while seconds > 0:
            print(f"{seconds}...")
            time.sleep(1)
            seconds-=1

    def chunk_list(self, input_list, chunk_size):
        for i in range(0, len(input_list), chunk_size):
            yield input_list[i:i + chunk_size]

    def find_non_ocred_keys(self, workflow):

        raw_imgs = [obj.key for obj in self.bucket.objects.filter(
            Prefix=f'raw/{workflow.slug}/'
        )]

        print(raw_imgs[0:5])

        # Replace .json with TIF, ocr/json with raw, and also get rid of SPLITPAGE component for images that have been split
        ocred_keys = [obj.key.replace('.json', '.tif').replace('ocr/json/', 'raw/') for obj in self.bucket.objects.filter(
            Prefix=f'ocr/json/{workflow.slug}/'
        )]

        # Add in originals to go with each splitpage
        splitpage_ocred_keys = [key for key in ocred_keys if 'SPLITPAGE' in key]
        splitpage_orig_keys = [re.sub(r'_SPLITPAGE_\d+', '', key) for key in splitpage_ocred_keys]

        print(ocred_keys[0:5])

        un_ocred_keys = set(raw_imgs) - set(ocred_keys) - set(splitpage_orig_keys)

        print(f"Found {len(un_ocred_keys)} out of {len(raw_imgs)} total raw images...")

        return un_ocred_keys

    def build_event(self, key):

        now = datetime.datetime.now().timestamp()

        return {
          "version": "0",
          "id": "17793124-05d4-b198-2fde-7ededc63b103",
          "detail-type": "Mapping Prejudice deed machine re-OCR",
          "source": "deedmachine.s3",
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

    def trigger_raw_put(self, workflow, raw_imgs):
        print("WARNING: ABOUT TO TRIGGER RAW FILE PUTS, WHICH MAY INCUR LARGE AWS CHARGES...")

        self.countdown()
        sfn_client = boto3.client('stepfunctions')

        for mk in raw_imgs:
            start_time = time.time()

            response = sfn_client.start_execution(
                stateMachineArn=settings.OCR_CLEANUP_STATE_MACHINE,
                name=f're_ocr_{uuid.uuid4().hex}',
                input=json.dumps(self.build_event(mk))
            )
            print(response)

            # If necessary, wait before completing
            if self.min_thread_time > 0:
                elapsed = time.time() - start_time
                time_remaining = self.min_thread_time - elapsed
                if time_remaining > 0:
                    print(f'Pausing {time_remaining} seconds')
                    time.sleep(time_remaining)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            if kwargs['mintime']:
                self.min_thread_time = kwargs['mintime']

            raw_imgs = self.find_non_ocred_keys(workflow)

            self.trigger_raw_put(workflow, raw_imgs)
