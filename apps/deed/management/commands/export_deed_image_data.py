import os
import datetime
import urllib

import pandas as pd

from django.core.management.base import BaseCommand
from django.db.models import Count, OuterRef, Subquery
from django.contrib.postgres.aggregates import StringAgg
from django.core import management
from django.conf import settings

from racial_covenants_processor.storage_backends import PrivateMediaStorage
from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.zoon.utils.zooniverse_load import get_image_url_prefix, get_full_url
from apps.deed.models import DeedPage, MatchTerm


class Command(BaseCommand):
    '''Export DeedPage data for transformation or analysis'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str, help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def save_manifest_local(self, df, version_slug):

        out_csv = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{version_slug}.csv")
        df.to_csv(out_csv, index=False)

        return out_csv

    def build_image_df(self, workflow):

        images = DeedPage.objects.filter(
            workflow=workflow
        ).values(
            'pk',
            'doc_num',
            'doc_alt_id',
            'doc_type',
            'book_id',
            'page_num',
            'split_page_num',
            'batch_id',
            'doc_date',
            'bool_match',
            'matched_terms__term',
            's3_lookup',
            'page_image_web'
        )

        images_df = pd.DataFrame.from_dict(images)
        images_df.rename(columns={'matched_terms__term': 'term'}, inplace=True)

        # Move matched_terms to list to de-dedupe
        images_term_aggregation = images_df[[
            's3_lookup',
            'term'
        ]].groupby('s3_lookup')['term'].agg(list).reset_index()

        images_df = images_df.drop(columns=['term']).drop_duplicates()
        images_df = images_df.merge(
            images_term_aggregation,
            how='left',
            on='s3_lookup'
        )

        first_image_url = images_df['page_image_web'].iloc[0]
        url_prefix = get_image_url_prefix(first_image_url)

        images_df['page_image_web'] = images_df['page_image_web'].apply(lambda x: get_full_url(url_prefix, x))

        return images_df

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            now = datetime.datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%M')

            deed_images_df = self.build_image_df(workflow)
            version_slug = f"{workflow.slug}_deedpage_list_{timestamp}"
            self.save_manifest_local(deed_images_df, version_slug)
