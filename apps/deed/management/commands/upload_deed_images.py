import os
import re
import glob
import boto3
import pandas as pd
from pathlib import Path, PurePosixPath
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
                            help='Load raw image list from cache')

        parser.add_argument('-p', '--pool', type=int,
                            help='How many threads to use? (Default is 8)')

    def gather_raw_image_paths(self, workflow_slug, deed_image_glob_root, deed_image_glob_remainder):
        print("Gathering all raw images paths for this workflow ...")
        print(os.path.join(deed_image_glob_root, deed_image_glob_remainder))
        raw_images = glob.glob(os.path.join(deed_image_glob_root, deed_image_glob_remainder), recursive=True)

        img_df = pd.DataFrame(raw_images, columns=['local_path'])
        img_df['remainder'] = img_df['local_path'].apply(lambda x: PurePosixPath(x).relative_to(deed_image_glob_root))
        img_df['filename'] = img_df['local_path'].apply(lambda x: Path(x).name)

        img_df['s3_path'] = img_df['remainder'].apply(
            lambda x: os.path.join('raw', workflow_slug, x)
        )
        return img_df

    def check_already_uploaded(self, workflow_slug, upload_keys):
        print("Checking s3 to see what images have already been uploaded...")
        s3 = self.session.resource('s3')

        key_filter = re.compile(f"raw/{workflow_slug}/.+\.tif")

        matching_keys = [obj.key for obj in self.bucket.objects.filter(
            Prefix=f'raw/{workflow_slug}/'
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
              'StorageClass': self.raw_storage_class
            })

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        load_from_cache = kwargs['cache']
        num_threads = kwargs['pool'] if kwargs['pool'] else 8

        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            workflow_slug = slugify(workflow_name)

            if kwargs['cache']:
                # Read option so you don't have to wait to crawl filesystem again
                try:
                    print("Attempting load from cached image list...")
                    raw_img_df = pd.read_csv(os.path.join(
                        settings.BASE_DIR, 'data', f"{workflow_slug}_raw_images_list.csv"))
                except:
                    print(
                        "Can't read cached file list. Try not using the --cache flag")
                    return False


            else:
                print(
                    "Scanning filesystem for local images using 'deed_image_glob_root', 'deed_image_glob_remainder' setting...")
                raw_img_df = self.gather_raw_image_paths(
                    workflow_slug,
                    workflow_config['deed_image_glob_root'],
                    workflow_config['deed_image_glob_remainder'])

                raw_img_df.to_csv(os.path.join(
                    settings.BASE_DIR, 'data', f"{workflow_slug}_raw_images_list.csv"), index=False)

            upload_keys = raw_img_df[[
                'local_path',
                's3_path'
            ]].to_dict('records')

            self.s3 = self.session.resource('s3')
            self.bucket = self.s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

            filtered_upload_keys = self.check_already_uploaded(
                workflow_slug, upload_keys)

            pool = ThreadPool(processes=num_threads)
            pool.map(self.upload_image, filtered_upload_keys)
