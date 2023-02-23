import os
import glob
import requests
from zipfile import ZipFile
#
from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings

from apps.plat.models import Subdivision
from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.parcel.utils.gis_utils import save_multipoly_instances
from apps.parcel.utils.parcel_utils import standardize_addition


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
        print(f"Downloading {shp_config['download_url']}...")

        base_filename = os.path.basename(shp_config['download_url'])
        local_download_path = os.path.join(self.shp_dir, base_filename)

        remote_file = requests.get(shp_config['download_url'], stream=True)
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

        with ZipFile(local_path, 'r') as zip_object:

            if file_prefix and file_prefix != '':
                file_list = zip_object.namelist()
                for member_file in file_list:
                    if re.match(rf"{shp_config['file_prefix']}\..+", member_file):
                        # Extract a single file from zip
                        zip_object.extract(member_file, os.path.join(
                            self.shp_dir, shp_config['file_prefix']))
                return os.path.join(self.shp_dir, shp_config['file_prefix'], f"{shp_config['file_prefix']}.shp")

            else:
                with ZipFile(local_path, 'r') as zip_obj:
                   # Extract all the contents of zip file in current directory
                   # This part needs more refinement with a different data set
                   zip_obj.extractall(self.shp_dir)
                   return os.path.join(self.shp_dir, glob.glob('*.shp', recursive=True)[0])

    def standardize_subdivisions(self, workflow):
        ''' Standardize each unique addition name, and save back to Subdivision objects with that plat_name'''
        print('Standardizing subdivision names...')

        subdivisions = Subdivision.objects.filter(
            workflow=workflow)
        subs_to_update = []
        for s in Subdivision.objects.filter(workflow=workflow).only('name', 'name_standardized'):
            s.name_standardized = standardize_addition(s.name)
            print(f'{s.name} --> {s.name_standardized}')
            subs_to_update.append(s)

        print(f'Updating {len(subs_to_update)} subdivisions ...')
        Subdivision.objects.bulk_update(
            subs_to_update, ['name_standardized'])

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            # This config info comes from local_settings, generally.
            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            workflow = get_workflow_obj(workflow_name)

            self.shp_dir = os.path.join(
                settings.BASE_DIR, 'data', 'shp', workflow.slug)

            for shp in self.batch_config['subdivision_shps']:
                if 'download_url' in shp:
                    local_shp = self.download_shp(workflow, shp)
                elif 'local_shp' in shp:
                    # Check if unzip needed
                    if os.path.splitext(shp['local_shp'])[1] == '.zip':
                        local_shp = self.unzip_files(shp['local_shp'], shp)
                    else:
                        local_shp = shp['local_shp']
                else:
                    print("No path to shapefile found. Exiting.")
                    raise

                print(
                    'Beginning homegrown layermapping: {} ...'.format(local_shp))

                required_attrs = ["feature_id", "name", "doc_num", "recorded_date"]

                save_multipoly_instances(
                    workflow,
                    Subdivision,
                    local_shp,
                    shp['mapping'],
                    required_attrs
                )

            self.standardize_subdivisions(workflow)
            management.call_command(
                'join_subdivisions_to_parcels', workflow=workflow_name)
            management.call_command(
                'rebuild_parcel_spatial_lookups', workflow=workflow_name)
