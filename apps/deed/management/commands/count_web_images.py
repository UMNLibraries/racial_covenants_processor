# import os
import re
import boto3
import datetime
import pandas as pd
from pathlib import PurePath

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Count

from apps.deed.models import DeedPage
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
             aws_session_token=getattr(settings, "AWS_SESSION_TOKEN", None))

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def find_matching_keys(self, workflow):
        print("Finding matching s3 keys...")
        # Then use the session to get the resource
        s3 = self.session.resource('s3')

        my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        matching_keys = [obj.key for obj in my_bucket.objects.filter(
            Prefix=f'web/{workflow.slug}/'
        )]

        return matching_keys

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            matching_keys = self.find_matching_keys(workflow)
            print(len(matching_keys))
