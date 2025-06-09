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

        hits_dir = f"ocr/hits_fuzzy/{workflow.slug}/"
        # key_filter = re.compile(f"ocr/hits/{workflow.slug}/.+\.json")
        key_filter = re.compile(f"{hits_dir}.+\.json")

        matching_keys = [obj.key for obj in my_bucket.objects.filter(
            # Prefix=f'ocr/hits/{workflow.slug}/'
            Prefix=hits_dir
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

    def build_match_report(self, workflow, matching_keys, test_file=None):
        '''Aggregate all the hits, their keys and terms into a single file'''

        with tempfile.TemporaryFile() as self.temp_ndjson:

            if not test_file:
                pool = ThreadPool(processes=12)
                pool.map(self.write_to_ndjson, matching_keys)

                self.temp_ndjson.seek(0)
                report_obj = ndjson.loads(self.temp_ndjson.read())
                report_df = pd.DataFrame(report_obj)
            else:
                # TEST
                report_obj = ndjson.loads(open(test_file, 'r').read())
                report_df = pd.DataFrame(report_obj)

            # Turn columns of terms into a list of terms found in each row
            # https://stackoverflow.com/questions/59487709/select-column-names-where-row-values-are-not-null-pandas-dataframe
            term_columns = report_df.drop(
                # 'expected_result' and 'bool_expected_match' are only present in test data
                columns=['workflow', 'lookup', 'uuid', 'expected_result', 'bool_expected_match'],
                errors='ignore'
            )
            report_df['matched_terms'] = term_columns.notna().dot(term_columns.columns+',').str.rstrip(',')

            report_df['num_terms'] = report_df['matched_terms'].apply(lambda x: len(x.split(',')))

            # create special flag for exceptions when they occur as the only term hit like "occupied by any" and "death certificate"
            bad_solo_terms = ["african", "any person of", "citizen", "descent", "extraction", "gentile", "hawaiian", "hindu", "indian", "irish", "italian", "malay", "malayan", "moorish", "mulatto", "mulato", "muslim", "nationality", "occupied by any", "oriental", "ottoman", "persian", "persons not of", "persons other than", "philippine", "polish", "racial", "said races", "servant", "syrian", "turkish", "used or occupied", "white or"]

            report_df['bad_solo_count'] = 0
            for term in bad_solo_terms:
                if term in report_df.columns:
                    report_df.loc[~report_df[term].isna(), 'bad_solo_count'] += report_df[term].apply(lambda x: self.split_or_1(x))

            # non-racial terms, for example as requested by CC County. If this is only term found, set as exception so it can be exported separately
            nonracial_terms = ['disorderly persons', 'less than 18 years', 'no children', 'no minor', 'occupy said real property', 'poverty', 'under the age of', 'years of age or older']

            report_df['nonracial_term_count'] = 0
            for term in nonracial_terms:
                if term in report_df.columns:
                    report_df.loc[~report_df[term].isna(), 'nonracial_term_count'] += report_df[term].apply(lambda x: self.split_or_1(x))

            report_df['deathcert_count'] = 0
            death_certs = ['death certificate', 'certificate of death', 'date of death', 'name of deceased', 'report of birth', 'certificate of hawaiian birth']
            for term in death_certs:
                if term in report_df.columns:
                    print(report_df[term].apply(lambda x: self.split_or_1(x)))

                    report_df.loc[~report_df[term].isna(), 'deathcert_count'] += report_df[term].apply(lambda x: self.split_or_1(x))

            report_df['military_count'] = 0
            military_terms = ['report of transfer', 'report of separation', 'transfer or discharge', 'blood group', 'notice of separation', 'place of separation', 'rank and classification', 'service no', 'was discharged from', 'date enlisted', 'enlisted record', 'honorable discharge', 'warrant at time of discharge', 'special military qualifications']

            for term in military_terms:
                if term in report_df.columns:
                    print(report_df[term].apply(lambda x: self.split_or_1(x)))

                    report_df.loc[~report_df[term].isna(), 'military_count'] += report_df[term].apply(lambda x: self.split_or_1(x))

            report_df['misc_exception_count'] = 0
            misc_exception_terms = ['minority business enterprise', 'nigger']

            for term in misc_exception_terms:
                if term in report_df.columns:
                    print(report_df[term].apply(lambda x: self.split_or_1(x)))

                    report_df.loc[~report_df[term].isna(), 'misc_exception_count'] += report_df[term].apply(lambda x: self.split_or_1(x))

            # Confusion terms: Sometimes there are fuzzy variations that cannot be eliminated
            # because you need the fuzziness, but are clearly not valid matches.
            # For example, "caucasian" with a fuzziness of 3 matches "canadian"
            # With confusion terms we'll attempt to let matches of "canadian" cancel out matches of "caucasian",
            #  and if no terms are left, then flag as an exception
            confusion_terms = [
                {'match_term': 'caucasian', 'confusion_term': 'canadian'},
                {'match_term': 'caucasian', 'confusion_term': 'calcasieu'},
                {'match_term': 'colored', 'confusion_term': 'dolored'},
                {'match_term': 'occupied by any', 'confusion_term': 'other than the applicant'}
            ]
            for term in confusion_terms:
                match_term = term['match_term']
                confusion_term = term['confusion_term']
                if match_term in report_df.columns and confusion_term in report_df.columns:
                    report_df.loc[
                        (~report_df[match_term].isna()) & (~report_df[confusion_term].isna()) & (report_df[match_term] <= report_df[confusion_term]),
                    'num_terms'] -= 2

                    # Now eliminate ones with the confusion term but NOT the match term
                    report_df.loc[
                        (report_df[match_term].isna()) & (~report_df[confusion_term].isna()),
                    'num_terms'] -= 1

            # Set bool_match to True, unless there's a suspect value or combination
            report_df['bool_match'] = True
            report_df['bool_exception'] = False
            report_df.loc[(report_df['num_terms'] == 1) & ((report_df['bad_solo_count'] > 0) | (report_df['nonracial_term_count'] > 0)), 'bool_match'] = False
            report_df.loc[(report_df['num_terms'] == 1) & ((report_df['bad_solo_count'] > 0) | (report_df['nonracial_term_count'] > 0)), 'bool_exception'] = True

            report_df.loc[(report_df['num_terms'] == 1) & (report_df['nonracial_term_count'] > 0), 'bool_match'] = False
            report_df.loc[(report_df['num_terms'] == 1) & (report_df['nonracial_term_count'] > 0), 'bool_exception'] = True

            # Death cert is an exception no matter how many other terms found
            report_df.loc[report_df['deathcert_count'] > 0, 'bool_match'] = False
            report_df.loc[report_df['deathcert_count'] > 0, 'bool_exception'] = True

            # Military record is an exception no matter how many other terms found
            report_df.loc[report_df['military_count'] > 0, 'bool_match'] = False
            report_df.loc[report_df['military_count'] > 0, 'bool_exception'] = True

            # Misc exceptions that are exception no matter how many other terms found
            report_df.loc[report_df['misc_exception_count'] > 0, 'bool_match'] = False
            report_df.loc[report_df['misc_exception_count'] > 0, 'bool_exception'] = True

            # If all match terms have been eliminated by confusion, exception
            report_df.loc[report_df['num_terms'] < 1, 'bool_match'] = False
            report_df.loc[report_df['num_terms'] < 1, 'bool_exception'] = True

            report_df.drop(columns=term_columns.columns, inplace=True)
            print(report_df)

            print(report_df[report_df['bool_match'] == True][['num_terms', 'bad_solo_count', 'matched_terms', 'bool_match', 'bool_exception']])    

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

        true_match_df = hits_df.loc[hits_df['bool_match'] == True]
        print(f"True match count: {len(true_match_df['lookup'].to_list())}")
        
        deed_hits = DeedPage.objects.filter(
            workflow=workflow,
            s3_lookup__in=true_match_df['lookup'].to_list()
        ).only('pk', 'page_image_web')

        num_deedpage_matches = deed_hits.count()
        if num_deedpage_matches > 0:
            # TODO: This is still getting the wrong number
            print(f'Found {num_deedpage_matches} matching DeedPage records. Setting bool_match to True...')
            deed_hits.update(bool_match=True)
        else:
            print("Couldn't find any matching DeedPage objects to set bool_match to True.")

        exceptions_df = hits_df.loc[hits_df['bool_exception'] == True]
        deed_exceptions = DeedPage.objects.filter(workflow=workflow, s3_lookup__in=exceptions_df['lookup'].to_list()).only('pk', 'page_image_web')

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
            print(f"{row['matched_terms']}: {len(row['lookups'])} pages")
            term, created = MatchTerm.objects.get_or_create(
                term=row['matched_terms']
            )
            objs = deed_objs_with_hits.filter(s3_lookup__in=row['lookups'])
            term.deedpage_set.add(*objs)

    def populate_highlight_images(self, workflow):
        print("Adding extrapolated highlight image paths to DeedPage...")
        # TODO: How to efficiently test if these actually exist
        pages_to_update = []
        for dp in DeedPage.objects.filter(workflow=workflow, bool_match=True).only('pk', 'page_image_web'):
            orig_img_file_name, orig_img_file_extension = os.path.splitext(dp.page_image_web.name)
            dp.page_image_web_highlighted = dp.page_image_web.name.replace('web/', 'web_highlighted/').replace(orig_img_file_extension, '__highlight.jpg')

            pages_to_update.append(dp)

        print(f'Adding highlight images for {len(pages_to_update)} hits ...')
        DeedPage.objects.bulk_update(
            pages_to_update, [f'page_image_web_highlighted'])

    def exempt_exceptions(self, workflow):
        print('Handling localized exceptions to racial term matches...')
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
            self.populate_highlight_images(workflow)
            self.exempt_exceptions(workflow)
