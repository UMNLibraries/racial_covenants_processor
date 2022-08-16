import os
import re
import boto3
import ndjson
import tempfile
import datetime
import pandas as pd

from django.core.management.base import BaseCommand
from django.core.files.base import File
from django.conf import settings

from apps.deed.models import DeedPage, MatchTerm, SearchHitReport
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

        parser.add_argument('-l', '--local', action='store_true',
                            help='Save to local csv in "main_exports" dir, rather than Django object/S3')

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
                columns=['workflow', 'lookup', 'uuid']
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

            return report_df

    def save_report_local(self, df, version_slug):
        out_csv = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{version_slug}.csv")
        df.to_csv(out_csv, index=False)

        return out_csv

    def save_report_model(self, df, version_slug, workflow, created_at):
        # export to .geojson temp file and serve it to the user
        with tempfile.NamedTemporaryFile() as tmp_file:
            # tmp_file_path = f'{version_slug}.csv'
            # df.to_geojson(tmp_file_path, index=False)
            df.to_csv(tmp_file, index=False)

            csv_export_obj = SearchHitReport(
                workflow=workflow,
                num_hits=df.shape[0],
                created_at = created_at
            )

            # Using File
            # with open(tmp_file, 'rb') as f:
            csv_export_obj.report_csv.save(f'{version_slug}.csv', File(tmp_file))
            csv_export_obj.save()
            return csv_export_obj

    def update_matches(self, workflow, matching_keys, hits_df):
        print('Looking for corresponding DeedPage objects ...')
        # web_img_keys = [key.replace('ocr/hits', 'web').replace('.json', '.jpg') for key in matching_keys]
        deed_hits = DeedPage.objects.filter(workflow=workflow, s3_lookup__in=hits_df[hits_df['bool_match'] == True]['lookup'].to_list()).only('pk', 'page_image_web')
        num_deedpage_matches = deed_hits.count()
        if num_deedpage_matches > 0:
            print(f'Found {num_deedpage_matches} matching DeedPage records. Setting bool_match to True...')
            deed_hits.update(bool_match=True)
        else:
            print("Couldn't find any matching DeedPage objects.")

        return deed_hits

    def add_matched_terms(self, workflow, deed_objs_with_hits, match_report):
        match_report['matched_terms'] = match_report['matched_terms'].apply(lambda x: x.split(','))
        exploded_df = match_report.explode('matched_terms')
        terms_grouped = exploded_df[[
            'lookup', 'matched_terms'
        ]].groupby('matched_terms')['lookup'].apply(list).reset_index(name='lookups')

        for index, row in terms_grouped.iterrows():
            print(row)
            term, created = MatchTerm.objects.get_or_create(
                term=row['matched_terms']
            )
            objs = deed_objs_with_hits.filter(s3_lookup__in=row['lookups'])
            term.deedpage_set.add(*objs)


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

            now = datetime.datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%M')
            version_slug = f"{workflow.slug}_hits_{timestamp}"

            if kwargs['local']:
                match_report_local = self.save_report_local(match_report, version_slug)
            else:
                # Save to geojson in Django storages/model
                match_report_obj = self.save_report_model(match_report, version_slug, workflow, now)

            print('Clearing previous bool_match values...')
            DeedPage.objects.filter(workflow=workflow).update(bool_match=False)

            deed_objs_with_hits = self.update_matches(workflow, matching_keys, match_report)

            self.add_matched_terms(workflow, deed_objs_with_hits, match_report)
