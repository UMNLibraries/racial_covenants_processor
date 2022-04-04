import re
import os
import glob
import requests
from zipfile import ZipFile

from django.core.management.base import BaseCommand
from django.conf import settings

from parcel.models import Parcel
from zoon.models import ZooniverseWorkflow
from zoon.utils.zooniverse_config import get_workflow_version


class Command(BaseCommand):
    '''Download and load a county parcel shapefile'''
    batch_config = None  # Set in handle
    shp_dir = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def download_shp(self, workflow, shp_config: object):
        '''
        Downloads a zipped (or not) parcel shapefile to this workflow's data/shp folder,
        renames based on an ID set in the workflow config, and unzips if necessary

        Arguments:
            workflow: ZooniverseWorkflow object
            shp_config: object from the workflow config including an id and download_url
        '''

        os.makedirs(self.shp_dir, exist_ok=True)
        print(shp_config['download_url'])
        remote_file = requests.get(shp_config['download_url'], stream=True)

        base_filename = os.path.basename(shp_config['download_url'])
        local_download_path = os.path.join(self.shp_dir, base_filename)
        with open(local_download_path, "wb") as outfile:
            for chunk in remote_file.iter_content(chunk_size=1024 * 10):
                if chunk:
                    outfile.write(chunk)
            outfile.close()

            # Check if unzip needed
            if os.path.splitext(local_download_path)[1] == '.zip':
                out_shp = self.unzip_files(local_download_path, shp_config)
                return out_shp

    def unzip_files(self, local_path, shp_config):
        '''
        Shapefiles are almost always downloaded as zipped files. Some zip files have many shapefiles that are not what we want, so an optional file_prefix helps determine which you want. If that prefix is null or blank it just returns the first .shp file it finds (this should probably be refined)
        Arguments:
            local_path: Local path to .zip file
            shp_config: object from the workflow config
        '''
        print(f'Unzipping {local_path}...')
        try:
            file_prefix = shp_config['file_prefix']
        except:
            file_prefix = False

        with ZipFile(local_path, 'r') as zipObject:

            if file_prefix and file_prefix != '':
                file_list = zipObject.namelist()
                for member_file in file_list:
                    if re.match(rf"{shp_config['file_prefix']}\..+", member_file):
                        # Extract a single file from zip
                        zipObject.extract(member_file, os.path.join(
                            self.shp_dir, shp_config['file_prefix']))
                return os.path.join(self.shp_dir, shp_config['file_prefix'], f"{shp_config['file_prefix']}.shp")

            else:
                with ZipFile(local_path, 'r') as zip_obj:
                   # Extract all the contents of zip file in current directory
                   # This part needs more refinement with a different data set
                   zip_obj.extractall(self.shp_dir)
                   return os.path.join(self.shp_dir, glob.glob('*.shp', recursive=True)[0])

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            # This config info comes from local_settings, generally.
            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            self.batch_dir = os.path.join(
                settings.BASE_DIR, 'data', 'zooniverse_exports', self.batch_config['panoptes_folder'])

            # Get workflow version from config yaml
            workflow_version = get_workflow_version(
                self.batch_dir, self.batch_config['config_yaml'])

            workflow = ZooniverseWorkflow.objects.get(
                workflow_name=workflow_name, version=workflow_version)

            self.shp_dir = os.path.join(
                settings.BASE_DIR, 'data', 'shp', workflow.slug)

            for shp in self.batch_config['parcel_shps']:
                local_shp = self.download_shp(workflow, shp)
                print(local_shp)
