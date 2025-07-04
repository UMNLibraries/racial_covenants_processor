import os
import datetime
import urllib
import boto3
import botocore
from multiprocessing.pool import ThreadPool

import pandas as pd
from random import sample

from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings

from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.zoon.utils.zooniverse_load import get_image_url_prefix, get_full_url
from apps.deed.models import DeedPage


class Command(BaseCommand):
    '''Export DeedPage data for transformation or analysis'''

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    s3 = session.resource('s3')

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str, help='Name of Zooniverse workflow to process, e.g. "Ramsey County"', required=True)

        parser.add_argument('-s', '--sample_pct', type=float, help='What percentage of total do you want to sample (0 to 1, 1 = 100%)? (required)', required=True)

    def save_manifest_local(self, df, version_slug):

        out_csv = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{version_slug}.csv")
        df.to_csv(out_csv, index=False)

        return out_csv

    def build_image_df(self, workflow, sample_pct):

        all_pks = DeedPage.objects.filter(
            workflow=workflow
        ).values_list('pk', flat=True)

        total_count = len(all_pks)
        sample_count = round(sample_pct * total_count)
        sample_pks = sample(list(all_pks), sample_count)

        images = DeedPage.objects.filter(
            workflow=workflow,
            pk__in=sample_pks
        ).select_related(
            'matched_terms__term',
        ).values(
            'pk',
            'doc_num',
            'doc_type',
            'book_id',
            'page_num',
            'batch_id',
            'doc_date',
            's3_lookup',
            'public_uuid',
            'page_image_web',
            'page_stats',
            'page_ocr_text',
            'page_ocr_json',
            'bool_match',
            'bool_exception',
            'page_image_web_highlighted',
        )

        images_df = pd.DataFrame.from_dict(images)
        images_df.rename(columns={'matched_terms__term': 'term'}, inplace=True)

        return images_df
    
    def bool_key_exists(self, key):
        '''Determine if s3 key exists'''
        try:
            self.s3.Object(settings.AWS_STORAGE_BUCKET_NAME, key).load()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                # The object does not exist.
                return False
            else:
                # Something else has gone wrong.
                raise
        else:
            # The object does exist.
            return True
    
    def add_columns(self, images_df):

        images_df['deed_machine_url'] = settings.PUBLIC_URL_ROOT + 'admin/deed/deedpage/' + images_df['pk'].astype(str) + '/change/'

        first_image_url = images_df['page_image_web'].iloc[0]
        url_prefix = get_image_url_prefix(first_image_url)

        # public urls
        for column in [
            'page_image_web',
            'page_image_web_highlighted',
        ]:
            images_df[column] = images_df[column].apply(lambda x: get_full_url(url_prefix, x))

        # keys that may or may not exist
        images_df['hit_key_basic'] = images_df['page_ocr_json'].str.replace('ocr/json','ocr/hits')
        images_df['hit_key_fuzzy'] = images_df['page_ocr_json'].str.replace('ocr/json','ocr/hits_fuzzy')

        return images_df
    
        # Define a function to be applied to each row
    def check_row_for_hits(self, row_obj):
        # Process the row here
        row = row_obj[1].to_dict()

        if self.bool_key_exists(row['hit_key_basic']):
            pass
        else:
            row['hit_key_basic'] = ''

        if self.bool_key_exists(row['hit_key_fuzzy']):
            pass
        else:
            row['hit_key_fuzzy'] = ''

        return row
    
    def check_for_hits(self, df):
        print('Starting parallel checks for hit files...')

        pool = ThreadPool(processes=12)
        result = pool.map(self.check_row_for_hits, df.iterrows())

        result_df = pd.DataFrame(result, columns=result[0].keys())

        pool.close()

        return result_df
    
    def reorder_columns(self, df):
        return df[[
            'pk',
            'deed_machine_url',
            'doc_num',
            'doc_type',
            'book_id',
            'page_num',
            'batch_id',
            'doc_date',
            's3_lookup',
            'public_uuid',
            'bool_match',
            'bool_exception',
            'page_image_web',
            'page_stats',
            'page_ocr_text',
            'page_ocr_json',
            'hit_key_basic',
            'hit_key_fuzzy',
            'page_image_web_highlighted',
        ]]

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        sample_pct = kwargs['sample_pct']

        workflow = get_workflow_obj(workflow_name)

        now = datetime.datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M')

        deed_images_df = self.build_image_df(workflow, sample_pct)
        deed_images_df = self.add_columns(deed_images_df)
        deed_images_df = self.check_for_hits(deed_images_df)
        deed_images_df = self.reorder_columns(deed_images_df)

        print(deed_images_df)
        version_slug = f"{workflow.slug}_deedpage_sample_{workflow.slug}_{round(100*sample_pct)}pct_{timestamp}"
        self.save_manifest_local(deed_images_df, version_slug)
