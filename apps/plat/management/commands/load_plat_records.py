import os
import boto3
import pandas as pd

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.plat.models import Plat, PlatMapPage
from apps.parcel.utils.parcel_utils import standardize_addition
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):

    raw_storage_class = 'GLACIER_IR'

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
             aws_session_token=getattr(settings, "AWS_SESSION_TOKEN", None))

    s3 = None
    bucket = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

        parser.add_argument('-m', '--manifest', type=str,
                            help='Path to manifest file listing plat maps (relative to data folder)')

    def make_s3_path(self, row, workflow_slug):
        if row['local_path'] and row['web_or_raw']:
            try:
                return os.path.join('plat', row['web_or_raw'], workflow_slug, row['filename'])
            except:
                return None
        return None

    def try_basename(self, x):
        try:
            return os.path.basename(x)
        except:
            return None

    def create_plat_objs(self, workflow, workflow_config):
        existing_lookup = {p['plat_name']: p['id'] for p in Plat.objects.filter(
            workflow=workflow).values('id', 'plat_name')}

        print(f"Found {len(existing_lookup)} existing Plat instances.")

        manifest_plats_df = pd.read_csv(
            workflow_config['plat_manifest'], dtype='object')

        import_columns = manifest_plats_df.columns.intersection(
            ['plat_name', 'plat_year', 'book_name', 'gov_id', 'local_path', 'remote_link', 'web_or_raw'])

        # Only retain columns we care about for Django
        manifest_plats_df = manifest_plats_df[import_columns]

        plats_to_upload = manifest_plats_df[~manifest_plats_df['plat_name'].isin(
            existing_lookup.keys())]
        plats_to_upload['workflow_id'] = workflow.id

        # Get distinct plats, rather than pages
        plats_to_upload = plats_to_upload.drop(
            columns=['local_path', 'remote_link', 'web_or_raw']).drop_duplicates()

        plats_to_upload['plat_name_standardized'] = plats_to_upload['plat_name'].apply(
            lambda x: standardize_addition(x))

        upload_objs = []
        for p in plats_to_upload.to_dict('records'):
            upload_objs.append(Plat(
                **p
            ))

        print(f'Creating {len(upload_objs)} new plat records ...')
        Plat.objects.bulk_create(upload_objs, batch_size=5000)

        return manifest_plats_df

    def create_plat_pages(self, manifest_df, workflow, workflow_config):
        plat_lookup = {p['plat_name']: p['id'] for p in Plat.objects.filter(
            workflow=workflow).values('id', 'plat_name')}

        existing_lookup = {p['plat__plat_name']: p['id'] for p in PlatMapPage.objects.filter(
            plat__workflow=workflow).values('id', 'plat__plat_name')}

        print(f"Found {len(existing_lookup)} existing PlatMapPage instances.")

        if 'filename' not in manifest_df.columns:
            manifest_df['filename'] = manifest_df['local_path'].apply(
                lambda x: self.try_basename(x))

        manifest_df['page_image_web'] = manifest_df.apply(
            self.make_s3_path, args=(workflow.slug,), axis=1)

        pages_to_upload = manifest_df[~manifest_df['plat_name'].isin(
            existing_lookup.keys())]
        pages_to_upload['plat_id'] = pages_to_upload['plat_name'].apply(
            lambda x: plat_lookup[x])

        upload_objs = []
        for p in pages_to_upload.drop(columns=['plat_name', 'book_name', 'local_path', 'filename', 'web_or_raw']).to_dict('records'):
            upload_objs.append(PlatMapPage(
                **p
            ))

        print(f'Creating {len(upload_objs)} new plat page records ...')
        PlatMapPage.objects.bulk_create(upload_objs, batch_size=5000)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']

        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            workflow = get_workflow_obj(workflow_name)

            if 'plat_manifest' in workflow_config:
                print(
                    f"Using manifest path from 'plat_manifest' value in workflow config: {workflow_config['plat_manifest']}")

                manifest_df = self.create_plat_objs(workflow, workflow_config)
                self.create_plat_pages(manifest_df, workflow, workflow_config)

            else:
                print(
                    "Missing manifest file. Try setting the 'plat_manifest' value in your workflow config.")
