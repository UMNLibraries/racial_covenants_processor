import os
import re
import csv
import json
import time
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
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
             aws_session_token=getattr(settings, "AWS_SESSION_TOKEN", None))

    s3 = session.resource('s3')

    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

    lambda_client = boto3.client('lambda')

    done_manifest_path = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def countdown(self, seconds=5):
        while seconds > 0:
            print(f"{seconds}...")
            time.sleep(1)
            seconds-=1

    def trigger_lambda(self, key):

        payload = json.dumps({
            'bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'key': key
        })

        response = self.lambda_client.invoke(
            FunctionName=settings.UPDATE_STATS_LAMBDA,
            InvocationType='Event',
            LogType='Tail',
            # ClientContext='string',
            Payload=payload
            # Qualifier='string'
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 202:
            with open(self.done_manifest_path, 'a') as done_manifest:
                done_manifest.write(key + '\n')
            return key
        return False

    def get_hit_jsons(self, workflow):
        matching_keys = [obj.key for obj in self.bucket.objects.filter(
            Prefix=f'ocr/hits/{workflow.slug}/'
        )]
        return matching_keys

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

    def trigger_raw_put(self, workflow):
        print("WARNING: ABOUT TO TRIGGER RAW FILE PUTS, WHICH MAY INCUR LARGE AWS CHARGES...")

        self.countdown()

        print(f'Gathering list of hit jsons in {workflow.slug} workflow ...')

        hit_jsons = self.get_hit_jsons(workflow)

        today = datetime.date.today().strftime('%Y%m%d')
        self.done_manifest_path = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{workflow.slug}_re-stats_complete_{today}.csv")

        # Filter out ones that already have been re-processed
        hit_jsons = self.check_already_processed(workflow.slug, hit_jsons)

        print(f'Found {len(hit_jsons)} matching images to trigger events on.')

        trigger_count = 0

        pool = ThreadPool(processes=12)
        pool.map(self.trigger_lambda, hit_jsons)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            self.trigger_raw_put(workflow)
