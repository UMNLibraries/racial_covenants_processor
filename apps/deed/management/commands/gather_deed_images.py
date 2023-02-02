# import os
import re
import boto3
import datetime
import numpy as np
import pandas as pd
from pathlib import PurePath

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Count

from apps.deed.models import DeedPage
from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.deed.utils.deed_pagination import tag_doc_num_page_counts
# from apps.deed.utils.deed_pagination import sort_doc_nums_by_page_count, update_docs_with_page_counts


class Command(BaseCommand):

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def find_matching_keys(self, workflow):
        print("Finding matching s3 keys...")
        # Then use the session to get the resource
        s3 = self.session.resource('s3')

        my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        key_filter = re.compile(f"ocr/stats/{workflow.slug}/.+\.json")

        matching_keys = [obj.key for obj in my_bucket.objects.filter(
            Prefix=f'ocr/stats/{workflow.slug}/'
        ) if re.match(key_filter, obj.key)]

        return matching_keys

    def add_supplemental_info(self, page_data_df, workflow):
        '''
        deed_supplemental_info': [
            {
                'data_csv': '/full/path/to/file.csv',
                'join_field_deed': 'doc_alt_id',
                'join_field_supp': 'itemnum',
                'mapping': {
                    'doc_num': 'docnum',
                    'doc_type': 'landtype'
                }
            }
        ],
        '''
        if 'deed_supplemental_info' in settings.ZOONIVERSE_QUESTION_LOOKUP[
            workflow.workflow_name]:
            print("Supplemental info to join found...")
            s_info_lookups = settings.ZOONIVERSE_QUESTION_LOOKUP[
                workflow.workflow_name
            ]['deed_supplemental_info']

            for s_info_lookup in s_info_lookups:
                s_df = pd.read_csv(s_info_lookup['data_csv'], dtype='object')

                join_field_supp = s_info_lookup['join_field_supp']

                # choose columns to keep
                cols_to_keep = list(s_info_lookup['mapping'].values()) + [join_field_supp]
                # drop unneeded columns
                s_df = s_df[cols_to_keep].drop_duplicates()

                # Avoid dropping join fields with the same name by renaming now
                if s_info_lookup['join_field_deed'] == join_field_supp:
                    s_df.rename(columns={join_field_supp: join_field_supp + '_right'}, inplace=True)
                    join_field_supp = join_field_supp + '_right'

                # rename to django col names, reverse keys and items for this step, but keep mapping in this order for consistency with other values being set in local_settings
                inv_map = {v: k for k, v in s_info_lookup['mapping'].items()}
                s_df.rename(columns=inv_map, inplace=True)
                page_data_df = page_data_df.merge(
                    s_df,
                    how="left",
                    left_on=s_info_lookup['join_field_deed'],
                    right_on=join_field_supp
                )

                page_data_df.drop(columns=[join_field_supp], inplace=True)

                # coalesce
                for field in list(s_info_lookup['mapping'].keys()):
                    if f'{field}_x' in page_data_df.columns:
                        page_data_df[field] = page_data_df[f'{field}_x'].combine_first(page_data_df[f'{field}_y'])
                        page_data_df.drop(columns=[f'{field}_x', f'{field}_y'], inplace=True)

            print(page_data_df)

            return page_data_df
        print("No supplemental info to join found, moving on.")
        return page_data_df


    def build_django_objects(self, matching_keys, workflow):
        '''
        Parses the list of s3 keys from this workflow and creates Django DeedPage instances, saves them to the database

        Arguments:
            matching_keys: List of s3 keys matching our workflow
            workflow: Django ZooniverseWorkflow object
        '''
        print("Extracting filename data from matching keys...")

        deed_pages = []

        # TODO: It would probably be more efficient to rewrite this loop in pandas
        for mk in matching_keys:
            try:
                deed_image_regex = settings.ZOONIVERSE_QUESTION_LOOKUP[
                    workflow.workflow_name]['deed_image_regex']
                page_data = re.search(
                    deed_image_regex, mk).groupdict()
                public_uuid = re.search(r'__([a-z0-9]+)\.json', mk).group(1)
                # print(page_data)
            except:
                print(f'Could not parse image path data: {mk}. You might need to adjust your deed_image_regex setting.')
                page_data = None

            if page_data:
                # We aren't using the slug, so delete before model import
                del page_data['workflow_slug']

                # Set image path and s3 lookup
                page_data['public_uuid'] = public_uuid
                page_data['s3_lookup'] = mk.replace(f"ocr/stats/{workflow.slug}/", "").replace(f"__{public_uuid}.json", "")

                page_data['page_stats'] = mk
                page_data['page_image_web'] = str(PurePath(mk).with_name(public_uuid + '.jpg')).replace("ocr/stats/", "web/")
                page_data['page_ocr_text'] = mk.replace("ocr/stats/", "ocr/txt/").replace(f"__{public_uuid}.json", ".txt")
                page_data['page_ocr_json'] = mk.replace("ocr/stats/", "ocr/json/").replace(f"__{public_uuid}.json", ".json")

                page_data['workflow_id'] = workflow.id

                if 'doc_date_year' in page_data:
                    page_data['doc_date'] = datetime.datetime(
                        int(page_data['doc_date_year']),
                        int(page_data['doc_date_month']),
                        int(page_data['doc_date_day']),
                    )
                    del page_data['doc_date_year']
                    del page_data['doc_date_month']
                    del page_data['doc_date_day']

                # Re-code bool_match as boolean if found. This likely is only a legacy feature since generally the OCR step will be done in the Lambda world and collected after this step.
                if 'bool_match' in page_data:
                    if page_data['bool_match']:
                        page_data['bool_match'] = True
                    else:
                        page_data['bool_match'] = False
                else:
                    page_data['bool_match'] = False
                # else:
                #     page_data['bool_match'] = False

                deed_pages.append(page_data)

        # dedupe
        deed_pages_df = pd.DataFrame(deed_pages)
        deed_pages_df = deed_pages_df.drop_duplicates(subset=['s3_lookup'])

        # Remove fake Nones
        # deed_pages_df[['page_num']].loc[df['shield'] > 35] = 0
        deed_pages_df['page_num'].replace('NONE', None, inplace=True)

        deed_pages_df = self.add_supplemental_info(deed_pages_df, workflow)

        # Drop duplicates again just in case
        deed_pages_df = deed_pages_df.drop_duplicates(subset=['s3_lookup'])

        # Tag docs with page count by doc_num
        print('Tagging doc num page counts...')
        deed_pages_df = tag_doc_num_page_counts(deed_pages_df)

        print(deed_pages_df.to_dict('records'))

        print("Creating Django DeedPage objects...")
        deed_pages = [DeedPage(**page_data) for page_data in deed_pages_df.to_dict('records')]
        print("Starting Django bulk_create...")
        DeedPage.objects.bulk_create(deed_pages, batch_size=10000)

        return deed_pages

    # def tag_deed_page_counts_sql(self, workflow):
    #     '''DEPRECATED: We tag each doc with the page count for each doc number to help with figuring out previous/next images.
    #     NOTE: This is not really the last word on the true "page number" for each deed, but rather
    #     a way to help create that pagination based on what we know about the data we received.
    #     See apps.deed.models.HitsDeedPageManager for more pagination/image steps. '''
    #     page_counts = get_doc_num_page_counts(workflow)
    #     page_count_records = sort_doc_nums_by_page_count(page_counts)
    #     update_docs_with_page_counts(workflow, page_count_records)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            print('Deleting old DeedPage records (but not their images)...')
            DeedPage.objects.filter(workflow=workflow).delete()

            matching_keys = self.find_matching_keys(workflow)

            image_objs = self.build_django_objects(
                matching_keys, workflow)

            # self.tag_deed_page_counts_sql(workflow)
