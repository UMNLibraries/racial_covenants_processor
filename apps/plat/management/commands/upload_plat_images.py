import os
import re
import glob
import boto3
import pandas as pd
from pathlib import Path
from multiprocessing.pool import ThreadPool

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.conf import settings


class Command(BaseCommand):

    raw_storage_class = 'GLACIER_IR'

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    s3 = None
    bucket = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

        parser.add_argument('-c', '--cache', action='store_true',
                            help='Load raw image list from cached filesystem scan')

        parser.add_argument('-o', '--overwrite', action='store_true',
                            help='Ignore previously uploaded keys and reupload all files (takes longer)')

        parser.add_argument('-p', '--pool', type=int,
                            help='How many threads to use? (Default is 8)')

    def gather_raw_plat_paths(self, plat_raw_glob):
        print("Gathering all raw images paths for this workflow ...")
        raw_images = glob.glob(plat_raw_glob)

        img_df = pd.DataFrame(raw_images, columns=['local_path'])
        # img_df['last_dir'] = img_df['local_path'].apply(
        #     lambda x: Path(x).parts[-2])
        # TODO: You could send part of the folder path or rewrite the filename as you create this in boto if there is worthwhile metadata like DEL number in the path
        img_df['filename'] = img_df['local_path'].apply(lambda x: Path(x).name)
        return img_df

    def check_already_uploaded(self, workflow_slug, upload_keys):
        print("Checking s3 to see what images have already been uploaded...")
        s3 = self.session.resource('s3')

        key_filter = re.compile(
            f"plat/web/{workflow_slug}/.+\.(?:tif|png|pdf|jpg)")

        matching_keys = [obj.key for obj in self.bucket.objects.filter(
            Prefix='plat/web'
        ) if re.match(key_filter, obj.key)]

        web_keys_to_check = [key['s3_path'] for key in upload_keys]

        # subtract already uploaded matching_keys from web_keys_to_check
        already_uploaded = set(web_keys_to_check).intersection(matching_keys)
        remaining_to_upload = [
            u for u in upload_keys if u['s3_path'] not in already_uploaded]
        print(
            f"Found {len(already_uploaded)} images already uploaded, {len(remaining_to_upload)} remaining...")

        return remaining_to_upload

    def upload_image(self, key_dict):
        print(f"Uploading {key_dict['s3_path']}")
        self.bucket.upload_file(
            key_dict['local_path'], key_dict['s3_path'], ExtraArgs={
              'StorageClass': self.raw_storage_class,
              'ContentType': 'image/jpeg'
            })

    def try_basename(self, x):
        try:
            return os.path.basename(x)
        except:
            return None

    def make_s3_path(self, row, workflow_slug):
        if row['local_path'] and row['web_or_raw']:
            try:
                return os.path.join('plat', row['web_or_raw'], workflow_slug, row['filename'])
            except:
                return None
        return None

    def prepare_manifest(self, workflow_slug, manifest_path):
        try:
            print("Attempting load from manifest file...")
            manifest_df = pd.read_csv(os.path.join(
                settings.BASE_DIR, 'data', manifest_path))
        except:
            print(
                "Can't read manifest. Is your file path correct, relative to the 'data' folder?")
            return None

        if 'filename' not in manifest_df.columns:
            manifest_df['filename'] = manifest_df['local_path'].apply(
                lambda x: self.try_basename(x))

        manifest_df['s3_path'] = manifest_df.apply(
            self.make_s3_path, args=(workflow_slug,), axis=1)

        return manifest_df

    def load_s3_pool(self, workflow_slug, manifest_df, num_threads, bool_overwrite=False):
        # Filter df to only rows with valid s3 paths
        upload_keys = manifest_df[~manifest_df['s3_path'].isna()][[
            'local_path',
            's3_path'
        ]].to_dict('records')

        self.s3 = self.session.resource('s3')
        self.bucket = self.s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        if bool_overwrite:
            print('Overwriting all keys, this will take longer...')
            filtered_upload_keys = upload_keys
        else:
            print('Filtering out previously uploaded keys...')
            filtered_upload_keys = self.check_already_uploaded(
                workflow_slug, upload_keys)

        pool = ThreadPool(processes=num_threads)
        pool.map(self.upload_image, filtered_upload_keys)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        cache = kwargs['cache']
        bool_overwrite = kwargs['overwrite']
        num_threads = kwargs['pool'] if kwargs['pool'] else 8

        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            workflow_slug = slugify(workflow_name)

            if 'plat_manifest' in workflow_config:
                print(
                    f"Using manifest path from 'plat_manifest' value in workflow config: {workflow_config['plat_manifest']}")
                manifest_df = self.prepare_manifest(
                    workflow_slug, workflow_config['plat_manifest'])
                if manifest_df is not None:
                    self.load_s3_pool(workflow_slug, manifest_df,
                                      num_threads, bool_overwrite)

            elif cache:
                # Not tested yet
                print(
                    "Scanning filesystem for local images using 'plat_raw_glob' setting...")
                raw_img_df = self.gather_raw_plat_paths(
                    workflow_config['plat_raw_glob'])

                raw_img_df.to_csv(os.path.join(
                    settings.BASE_DIR, 'data', f"{workflow_slug}_raw_plats_list.csv"), index=False)

                self.load_s3_pool(workflow_slug, raw_img_df,
                                  num_threads, bool_overwrite)
