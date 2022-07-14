import os
import re
import boto3
import ndjson
import tempfile
import pandas as pd

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.deed.models import DeedPage, SearchHitReport
# from apps.zoon.models import ZooniverseSubject
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def find_matching_keys(self, workflow):
        print("Finding matching s3 keys...")
        s3 = self.session.resource('s3')

        my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        key_filter = re.compile(f"ocr/hits/{workflow.slug}/.+\.json")

        matching_keys = [obj.key for obj in my_bucket.objects.filter(
            Prefix=f'ocr/hits/{workflow.slug}/'
        ) if re.match(key_filter, obj.key)]

        return matching_keys

    def build_match_report(self, workflow, matching_keys):
        '''Aggregate all the hits, their keys and terms into a single file'''

        s3 = self.session.client('s3')
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        with tempfile.TemporaryFile() as temp_ndjson:

            for key in matching_keys:
                content_object = s3.get_object(Bucket=bucket, Key=key)
                file_content = content_object['Body'].read()  # Keeping it in binary, not decoding
                temp_ndjson.write(file_content + b'\n')

            temp_ndjson.seek(0)
            report_obj = ndjson.loads(temp_ndjson.read())
            report_df = pd.DataFrame(report_obj)

            # Turn columns of terms into a list of terms found in each row
            # https://stackoverflow.com/questions/59487709/select-column-names-where-row-values-are-not-null-pandas-dataframe
            term_columns = report_df.drop(
                columns=['workflow', 'lookup']
            )
            report_df['matched_terms'] = term_columns.notna().dot(term_columns.columns+',').str.rstrip(',')

            report_df['num_terms'] = report_df['matched_terms'].apply(lambda x: len(x.split(',')))

            # create special flag for multiple occurences of "white"
            if 'white' in report_df.columns:
                report_df.loc[~report_df['white'].isna(), 'white_count'] = report_df['white'].apply(lambda x: len(x))
            else:
                report_df['white_count'] = 0

            # Set bool_match to True, unless there's a suspect only white value
            report_df['bool_match'] = True
            report_df.loc[(report_df['num_terms'] == 1) & (report_df['white_count'] > 1), 'bool_match'] = False

            report_df.drop(columns=term_columns.columns, inplace=True)
            print(report_df)

    # def update_matches(self, workflow, matching_keys):
    #     print('Looking for corresponding DeedPage objects ...')
    #     web_img_keys = [key.replace('ocr/hits', 'web').replace('.json', '.jpg') for key in matching_keys]
    #     deed_hits = DeedPage.objects.filter(workflow=workflow, page_image_web__in=web_img_keys).only('pk', 'page_image_web')
    #     num_deedpage_matches = deed_hits.count()
    #     if num_deedpage_matches > 0:
    #         print(f'Found {num_deedpage_matches} matching DeedPage records. Setting bool_match to True...')
    #         deed_hits.update(bool_match=True)
    #     else:
    #         print("Couldn't find any matching DeedPage objects.")
    #
    #     return deed_hits
    #     # maybe loop through found terms?



    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:

            workflow = get_workflow_obj(workflow_name)
            print(workflow.slug)

            matching_keys = self.find_matching_keys(workflow)
            print(matching_keys)

            match_report = self.build_match_report(workflow, matching_keys)

            # deed_hits = self.update_matches(workflow, matching_keys)

            # image_objs = self.build_django_objects(
            #     matching_keys, workflow)

            # TODO: Move this to separate management command to be run post-Zooniverse
            # self.join_to_subjects(workflow)
