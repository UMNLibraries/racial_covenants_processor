import os
import re
import boto3
import json
import ndjson
import tempfile
import datetime
import pandas as pd
from multiprocessing.pool import ThreadPool

from django.core.management.base import BaseCommand
from django.core.files.base import File
from django.db.models import Count
from django.conf import settings

from apps.deed.models import DeedPage, MatchTerm, SearchHitReport
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

        print(f"Found {len(matching_keys)} matching hit objects.")
        return matching_keys

    def split_or_1(self, x):
        try:
            return len(x)
        except:
            return 1

    def write_to_ndjson(self, key):
        content_object = self.s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
        file_content = content_object['Body'].read()  # Keeping it in binary, not decoding
        self.temp_ndjson.write(file_content + b'\n')

    def build_match_report(self, workflow, matching_keys):
        '''Aggregate all the hits, their keys and terms into a single file'''

        with tempfile.TemporaryFile() as self.temp_ndjson:

            pool = ThreadPool(processes=12)
            pool.map(self.write_to_ndjson, matching_keys)

            self.temp_ndjson.seek(0)
            report_obj = ndjson.loads(self.temp_ndjson.read())
            report_df = pd.DataFrame(report_obj)

            # Turn columns of terms into a list of terms found in each row
            # https://stackoverflow.com/questions/59487709/select-column-names-where-row-values-are-not-null-pandas-dataframe
            term_columns = report_df.drop(
                columns=['workflow', 'lookup', 'uuid']
            )
            report_df['matched_terms'] = term_columns.notna().dot(term_columns.columns+',').str.rstrip(',')

            report_df['num_terms'] = report_df['matched_terms'].apply(lambda x: len(x.split(',')))

            # create special flag for exceptions like "occupied by any" and "death certificate"
            if 'occupied by any' in report_df.columns:
                print(report_df['occupied by any'].apply(lambda x: self.split_or_1(x)))

                report_df.loc[~report_df['occupied by any'].isna(), 'occupied_count'] = report_df['occupied by any'].apply(lambda x: self.split_or_1(x))
            else:
                report_df['occupied_count'] = 0

            if 'citizen' in report_df.columns:
                print(report_df['citizen'].apply(lambda x: self.split_or_1(x)))

                report_df.loc[~report_df['citizen'].isna(), 'citizen_count'] = report_df['citizen'].apply(lambda x: self.split_or_1(x))
            else:
                report_df['citizen_count'] = 0

            report_df['deathcert_count'] = 0
            death_certs = ['death certificate', 'certificate of death', 'date of death', 'name of deceased']
            for term in death_certs:
                if term in report_df.columns:
                    print(report_df[term].apply(lambda x: self.split_or_1(x)))

                    report_df.loc[~report_df[term].isna(), 'deathcert_count'] = report_df[term].apply(lambda x: self.split_or_1(x))

            report_df['military_count'] = 0
            military_terms = ['report of transfer', 'report of separation', 'transfer or discharge', 'blood group']
            for term in military_terms:
                if term in report_df.columns:
                    print(report_df[term].apply(lambda x: self.split_or_1(x)))

                    report_df.loc[~report_df[term].isna(), 'military_count'] = report_df[term].apply(lambda x: self.split_or_1(x))
                   

            # Set bool_match to True, unless there's a suspect value or combination
            report_df['bool_match'] = True
            report_df['bool_exception'] = False
            report_df.loc[(report_df['num_terms'] == 1) & (report_df['occupied_count'] > 0), 'bool_match'] = False
            report_df.loc[(report_df['num_terms'] == 1) & (report_df['occupied_count'] > 0), 'bool_exception'] = True

            report_df.loc[(report_df['num_terms'] == 1) & (report_df['citizen_count'] > 0), 'bool_match'] = False
            report_df.loc[(report_df['num_terms'] == 1) & (report_df['citizen_count'] > 0), 'bool_exception'] = True

            # Death cert is an exception no matter how many other terms found
            report_df.loc[report_df['deathcert_count'] > 0, 'bool_match'] = False
            report_df.loc[report_df['deathcert_count'] > 0, 'bool_exception'] = True

            # Military record is an exception no matter how many other terms found
            report_df.loc[report_df['military_count'] > 0, 'bool_match'] = False
            report_df.loc[report_df['military_count'] > 0, 'bool_exception'] = True

            report_df.drop(columns=term_columns.columns, inplace=True)
            print(report_df)

            return report_df

    def save_report_local(self, df, version_slug):
        out_csv = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{version_slug}.csv")
        df.to_csv(out_csv, index=False)

        return out_csv

    def save_report_model(self, df, version_slug, workflow, created_at):
        with tempfile.NamedTemporaryFile() as tmp_file:
            df.to_csv(tmp_file, index=False)

            csv_export_obj = SearchHitReport(
                workflow=workflow,
                num_hits=df[df['bool_match'] == True].shape[0],
                num_exceptions=df[df['bool_exception'] == True].shape[0],
                created_at = created_at
            )

            csv_export_obj.report_csv.save(f'{version_slug}.csv', File(tmp_file))
            csv_export_obj.save()
            return csv_export_obj

    def update_matches(self, workflow, matching_keys, hits_df):
        print('Looking for corresponding DeedPage objects ...')
        deed_hits = DeedPage.objects.filter(
            workflow=workflow,
            s3_lookup__in=hits_df[hits_df['bool_match'] == True]['lookup'].to_list()
        ).only('pk', 'page_image_web')

        num_deedpage_matches = deed_hits.count()
        if num_deedpage_matches > 0:
            print(f'Found {num_deedpage_matches} matching DeedPage records. Setting bool_match to True...')
            deed_hits.update(bool_match=True)
        else:
            print("Couldn't find any matching DeedPage objects to set bool_match to True.")

        deed_exceptions = DeedPage.objects.filter(workflow=workflow, s3_lookup__in=hits_df[hits_df['bool_exception'] == True]['lookup'].to_list()).only('pk', 'page_image_web')

        print('Looking for corresponding DeedPage objects for exceptions...')
        num_deedpage_exceptions = deed_exceptions.count()
        if num_deedpage_exceptions > 0:
            print(f'Found {num_deedpage_exceptions} matching DeedPage records. Setting bool_exception to True...')
            deed_exceptions.update(bool_exception=True)
        else:
            print("Couldn't find any matching DeedPage objects to set bool_exception to True.")

        return deed_hits | deed_exceptions

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

    def exempt_exceptions(self, workflow):
        print('Handling exceptions to racial term matches...')
        s3 = self.session.client('s3')
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        if 'term_exceptions' in settings.ZOONIVERSE_QUESTION_LOOKUP[workflow.workflow_name]:
            exceptions = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow.workflow_name]['term_exceptions']
            for term in exceptions.keys():
                print(term)
                term_pages = DeedPage.objects.filter(workflow=workflow, matched_terms__term=term).annotate(num_terms=Count('matched_terms'))

                for page in term_pages:
                    num_terms = page.num_terms
                    ocr_json = s3.get_object(Bucket=bucket, Key=page.page_ocr_text.name)
                    page_text = str(ocr_json['Body'].read()).lower()
                    for e in exceptions[term]:
                        e_count = page_text.count(e.lower())
                        if e_count > 0:
                            num_terms -= 1

                    if num_terms <= 0:
                        # TODO: Change to bulk update or, better, incorporate into original term search
                        page.bool_exception = True
                        page.bool_match = False
                        page.save()

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:

            workflow = get_workflow_obj(workflow_name)

            matching_keys = self.find_matching_keys(workflow)

            match_report = self.build_match_report(workflow, matching_keys)

            now = datetime.datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%M')
            version_slug = f"{workflow.slug}_hits_{timestamp}"

            if kwargs['local']:
                match_report_local = self.save_report_local(match_report, version_slug)
            else:
                # Save to csv in Django storages/model
                match_report_obj = self.save_report_model(match_report, version_slug, workflow, now)

            print('Clearing previous bool_match and bool_exception values...')
            DeedPage.objects.filter(workflow=workflow, bool_match=True).update(bool_match=False)
            DeedPage.objects.filter(workflow=workflow, bool_exception=True).update(bool_exception=False)

            deed_objs_with_hits = self.update_matches(workflow, matching_keys, match_report)

            self.add_matched_terms(workflow, deed_objs_with_hits, match_report)
            self.exempt_exceptions(workflow)
