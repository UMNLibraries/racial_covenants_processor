import os
import re
import datetime
import boto3
import shutil

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.parcel.utils.export_utils import build_metes_and_bounds_df


class Command(BaseCommand):
    '''Dump a CSV and zipped file of high-rez DeedPage images with metes and bounds'''

    s3 = boto3.client('s3')

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        
        parser.add_argument('-n', '--num_subjects', type=int, default=50,
                            help='Number of ZooniverseSubjects to export. Default is 50.')

    def save_csv_local(self, df, workflow, timestamp):
        out_csv = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{workflow.slug}-metes-and-bounds-{timestamp}.csv")
        df.to_csv(out_csv, index=False)

        return out_csv

    def save_original_image_local(self, workflow, download_folder, s3_lookup):

        test_exts = ["tif", "jpg", "TIF", "JPG", "JPEG"]
        for ext in test_exts:
            object_key = f"raw/{workflow.slug}/{s3_lookup}.{ext}"
            # Remove splitpage, e.g. if it's a multipage image, try to find the original
            object_key = re.sub(r"_SPLITPAGE_\d+", "", object_key)
            local_path = os.path.join(download_folder, os.path.basename(object_key))
            print(object_key)

            try:
                self.s3.download_file(settings.AWS_STORAGE_BUCKET_NAME, object_key, local_path)
                print(f"Image '{object_key}' downloaded successfully to '{local_path}'")

                return local_path.replace(f"{download_folder}/", '')
            except Exception as e:
                print(f"Error downloading image: {e}")
        return None
    
    def zip_orig_images(self, download_folder):
        try:
            shutil.make_archive(download_folder, 'zip', root_dir=download_folder)
            print(f"Successfully created '{download_folder}.zip'")

        except Exception as e:
            print(f"An error occurred: {e}")

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        num_subjects = kwargs['num_subjects']

        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
            return False
        else:
            workflow = get_workflow_obj(workflow_name)

        df = build_metes_and_bounds_df(workflow, num_subjects)

        if df.shape[0] == 0:
            print('No metes and bounds subjects found in workflow.')
            return False

        timestamp = datetime.datetime.now().strftime('%Y%m%d')

        download_folder = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{workflow.slug}-metes-and-bounds-{timestamp}_images"
        )
        os.makedirs(download_folder, exist_ok=True)

        df['orig_image'] = df['image_lookup'].apply(lambda x: self.save_original_image_local(workflow, download_folder, x))

        print(df)

        self.zip_orig_images(download_folder)
        self.save_csv_local(df, workflow, timestamp)
