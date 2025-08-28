import os
import re
import boto3
import datetime
import random
import numpy as np
import pandas as pd
from pathlib import PurePath
# from itertools import batched

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Count

from apps.deed.models import DeedPage
from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.deed.utils.deed_pagination import paginate_deedpage_df


class Command(BaseCommand):

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        
    def chunk_list(self, input_list, chunk_size):
            return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]
        
    def delete_existing_dps(self, workflow):
        print('Deleting old DeedPage records (but not their images)...')

        dp_pks = DeedPage.objects.filter(workflow=workflow).values_list('pk', flat=True)
        delete_count = 0
        chunk_size = 10000
        for chunk in self.chunk_list(dp_pks, chunk_size):
            DeedPage.objects.filter(pk__in=chunk).delete()
            delete_count += chunk_size
            print(f"Deleted {delete_count} records...")

    def find_matching_keys(self, workflow):
        print("Finding matching s3 keys...")
        # Then use the session to get the resource
        s3 = self.session.resource('s3')

        my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        # TODO: Eliminate this conditional once new Ramsey records are OCRed under new system
        if workflow.workflow_name == 'Ramsey County':
            key_filter = re.compile(f"web/{workflow.slug}/.+\.jpg")

            matching_keys = [obj.key for obj in my_bucket.objects.filter(
                Prefix=f'web/{workflow.slug}/'
            ) if re.match(key_filter, obj.key)]

        else:
            key_filter = re.compile(f"ocr/stats/{workflow.slug}/.+\.json")

            matching_keys = [obj.key for obj in my_bucket.objects.filter(
                Prefix=f'ocr/stats/{workflow.slug}/'
            ) if re.match(key_filter, obj.key)]

        return matching_keys
    
    def add_merge_fields(self, page_data_df, workflow):
        '''Build field from components in regex. Note that for now components and component regex capture groups must be expected values
        'merge_fields': {
            'field_to_overwrite': {'fields': ['component_field_1', 'component_field_2'], 'separator': 'sep_character', 'replace_nulls': False}  # Format
            'doc_num': {'fields': ['doc_type', 'doc_num'], 'separator': '', 'replace_nulls': False}  # Example
        },  # Build field from components in regex

        '''
        if 'merge_fields' in settings.ZOONIVERSE_QUESTION_LOOKUP[workflow.workflow_name]:
            merge_fields = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow.workflow_name]['merge_fields']

            print("Merge field(s) found...")

            for mf_key, mf_obj in merge_fields.items():
                page_data_df[mf_obj['fields']] = page_data_df[mf_obj['fields']].fillna('')
                if mf_obj['replace_nulls'] == True:
                    page_data_df[mf_key] = page_data_df[mf_obj['fields']].astype(str).agg(mf_obj['separator'].join, axis=1)
                else:
                    page_data_df.loc[~page_data_df[mf_key].isin(['NONE', None, '', np.NaN]), [mf_key]] = page_data_df[mf_obj['fields']].astype(str).agg(mf_obj['separator'].join, axis=1)

            return page_data_df
        
        else:
            print("No merge fields found, moving on.")
            return page_data_df

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

                join_fields_supp = s_info_lookup['join_fields_supp']

                # choose columns to keep
                cols_to_keep = list(set(list(s_info_lookup['mapping'].values()) + join_fields_supp))
                # drop unneeded columns
                s_df = s_df[cols_to_keep].drop_duplicates()

                # Avoid dropping join fields with the same name by renaming now
                if s_info_lookup['join_fields_deed'] == join_fields_supp:
                    s_df.rename(columns={field: field + '_right' for field in join_fields_supp}, inplace=True)
                    join_fields_supp = [field + '_right' for field in join_fields_supp]

                # rename to django col names, reverse keys and items for this step, but keep mapping in this order for consistency with other values being set in local_settings
                inv_map = {v: k for k, v in s_info_lookup['mapping'].items()}
                s_df.rename(columns=inv_map, inplace=True)
                page_data_df = page_data_df.merge(
                    s_df,
                    how="left",
                    left_on=s_info_lookup['join_fields_deed'],
                    right_on=join_fields_supp
                )

                page_data_df.drop(columns=join_fields_supp, inplace=True)

                # coalesce
                for field in list(s_info_lookup['mapping'].keys()):
                    if f'{field}_x' in page_data_df.columns:
                        page_data_df[field] = page_data_df[f'{field}_x'].combine_first(page_data_df[f'{field}_y'])
                        page_data_df.drop(columns=[f'{field}_x', f'{field}_y'], inplace=True)

            return page_data_df
        else:
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
        # print(random.sample(matching_keys, 100))
        for mk in matching_keys:
            try:
                deed_image_regex = settings.ZOONIVERSE_QUESTION_LOOKUP[
                    workflow.workflow_name]['deed_image_regex']
                page_data = re.search(
                    deed_image_regex, mk).groupdict()

                # TODO: Eliminate this conditional once new Ramsey records are OCRed under new system
                if workflow.workflow_name == 'Ramsey County':
                    public_uuid = ''
                else:
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
                # # In order to associate doc numbers with a file that has been split with splitpages, you need to join with an original file lookup, rather than the final s3_lookup created by the lambda process.
                # page_data['orig_file_lookup'] = re.sub(r'_SPLITPAGE_\d+', '', page_data['s3_lookup'])
                # # print(page_data['orig_file_lookup'])

                page_data['page_stats'] = mk

                # TODO: Eliminate this conditional once new Ramsey records are OCRed under new system
                if workflow.workflow_name == 'Ramsey County':
                    page_data['page_image_web'] = mk
                    page_data['page_ocr_text'] = ''
                    page_data['page_ocr_json'] = ''
                else:
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

                deed_pages.append(page_data)

        # dedupe
        deed_pages_df = pd.DataFrame(deed_pages)
        deed_pages_df = deed_pages_df.drop_duplicates(subset=['s3_lookup'])

        print(deed_pages_df)

        deed_pages_df = self.add_merge_fields(deed_pages_df, workflow)
        deed_pages_df = self.add_supplemental_info(deed_pages_df, workflow)

        # Drop duplicates again just in case
        deed_pages_df = deed_pages_df.drop_duplicates(subset=['s3_lookup'])

        # Tag docs with prev/next page images
        print('Tagging prev/next photos...')
        deed_pages_df = paginate_deedpage_df(deed_pages_df)

        return deed_pages_df
    
    def save_unprocessed_deed_pages(self, workflow, df):
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M')
        version_slug = f"{workflow.slug}_deedpages_{timestamp}"
        out_deed_page_csv = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{version_slug}.csv")

        df.to_csv(out_deed_page_csv, index=False)

        return out_deed_page_csv
    
    def import_to_django_csv_copy(self, csv_path, workflow):

        print("Starting Django copy create...")
        DeedPage.objects.from_csv(
            csv_path,
            force_not_null=['doc_alt_id'],
            static_mapping={
                'bool_exception': False,
                'bool_manual': False
            }
        )

        image_obj_count = DeedPage.objects.filter(workflow=workflow).count()
        print(f'Successfully created {image_obj_count} DeedPage objects.')

        return image_obj_count


    # def import_to_django(self, deed_pages_df, workflow):

    #     print("Creating Django DeedPage objects...")
    #     deed_pages = [DeedPage(**page_data) for page_data in deed_pages_df.to_dict('records')]
    #     print("Starting Django bulk_create...")
    #     DeedPage.objects.bulk_create(deed_pages, batch_size=10000)

    #     return deed_pages

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            self.delete_existing_dps(workflow)

            matching_keys = self.find_matching_keys(workflow)

            deed_page_df = self.build_django_objects(matching_keys, workflow)

            out_csv_path = self.save_unprocessed_deed_pages(workflow, deed_page_df)

            # out_csv_path = os.path.join(
            # settings.BASE_DIR, 'data', 'main_exports', 'ca-contra-costa-county_deedpages_20250403_0605.csv')

            image_obj_count = self.import_to_django_csv_copy(out_csv_path, workflow)

            # image_objs = self.import_to_django(
            #     deed_page_df, workflow)
