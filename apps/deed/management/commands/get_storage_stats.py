# import os
import re
import ndjson
import tempfile
import boto3
import datetime
import pandas as pd

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Count

from apps.deed.models import DeedPage
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):

    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    s3 = session.client('s3')
    temp_ndjson = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def find_matching_keys(self, workflow, prefix):
        print(f'Finding matching {prefix} s3 keys...')
        # Then use the session to get the resource
        s3 = self.session.resource('s3')

        my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        matching_keys = [{'prefix': prefix, 'key': obj.key, 'size': obj.size} for obj in my_bucket.objects.filter(
            Prefix=f'{prefix}/{workflow.slug}/'
        )]

        return matching_keys

    # def write_to_ndjson(self, key):
    #     content_object = self.s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
    #     size = content_object.size
    #     self.temp_ndjson.write('"' + key + '"' + '|' + size + b'\n')

    # def build_storage_stats(self, workflow, matching_keys):
    #     '''Aggregate all the hits, their keys and terms into a single file'''

    #     with tempfile.TemporaryFile() as self.temp_ndjson:

    #         pool = ThreadPool(processes=12)
    #         pool.map(self.write_to_ndjson, matching_keys)

    #         self.temp_ndjson.seek(0)
    #         report_obj = ndjson.loads(self.temp_ndjson.read())
    #         report_df = pd.DataFrame(report_obj)

    # def build_storage_stats(self, workflow, matching_keys):

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            dfs = []
            for prefix in ['raw', 'web', 'ocr/json', 'ocr/stats', 'ocr/txt', 'ocr/hits']:

                matching_keys = self.find_matching_keys(workflow, prefix)

                temp_df = pd.DataFrame.from_records(matching_keys)
                dfs.append(temp_df)
            
            df = pd.concat(dfs)

            print(df.shape)

            stats_df = df.groupby('prefix').agg(
                file_count=('size', 'count'),
                total_size=('size', 'sum'),
                median_size=('size', 'median'),
                mean_size=('size', 'mean'),
            ).reset_index()

            print(stats_df)
