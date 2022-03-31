import os
import requests

from django.core.management.base import BaseCommand
from django.conf import settings

from parcel.models import Parcel
from zoon.models import ZooniverseWorkflow
from zoon.utils.zooniverse_config import get_workflow_version


class Command(BaseCommand):
    '''Download and load a county parcel shapefile'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def download_shp(self, workflow, shp_url, zipped=True):
        shp_dir = os.path.join(settings.BASE_DIR, 'data', 'shp', workflow.slug)
        os.makedirs(shp_dir, exist_ok=True)
        print(shp_url)
        remote_file = requests.get(shp_url, stream=True)

        with open(os.path.join(shp_dir, os.path.basename(shp_url)), "wb") as outfile:
            for chunk in remote_file.iter_content(chunk_size=1024 * 10):
                if chunk:
                    outfile.write(chunk)

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

            parcel_shp_remote = self.batch_config['parcel_shp_remote']
            self.download_shp(workflow, parcel_shp_remote)
