import re
import os
import glob
import datetime
import requests
from zipfile import ZipFile

from django.core.management.base import BaseCommand
from django.core import management
from django.contrib.gis.gdal import DataSource, OGRGeometry, OGRGeomType
from django.contrib.gis.gdal.error import GDALException
from django.conf import settings

from apps.parcel.models import Parcel, ParcelJoinCandidate
from apps.plat.models import Plat, PlatAlternateName
from apps.parcel.utils.parcel_utils import standardize_addition, get_all_parcel_options
from apps.zoon.utils.zooniverse_config import get_workflow_obj


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

    def remove_z(self, wkt):
        ''' Remove Z dimension from WKT. '''
        z_search = r'([-\d\.]+) ([-\d\.]+) ([-\d\.]+)'
        return re.sub(z_search, r'\1 \2', wkt)

    def gather_all_attributes(self, field_list, feat):
        ''' Go through each of the attributes in the shapefile, create a JSON object of them all, then put in a single kitchen-sink attribute on the matching Django instance. '''

        data = {}
        for field in field_list:
            data[field] = feat.get(field)
            if type(data[field]) in [datetime.date, datetime.datetime]:
                try:
                    data[field] = data[field].strftime('%Y-%m-%d')
                except:
                    data[field] = data[field].isoformat()

        return data

    def build_mapping(self, config):
        ''' Construct a layermapping-ready mapping from the CSV'''
        mapping = {}
        for attr in ["pin_primary", "pin_secondary", "street_address", "city",
                     "state", "zip_code", "county_name", "county_fips", "plat_name",
                     "block", "lot", "join_description", "phys_description",
                     "township", "range", "section"]:
            if config[attr] != '':
                mapping.update({attr: config[attr]})
        return mapping

    def save_parcels(self, workflow, shp_path, shp_mapping):
        parcels = []
        parcel_count = 0

        orig_filename = os.path.basename(shp_path)
        ds = DataSource(shp_path)
        layer = ds[0]
        mapping = self.build_mapping(shp_mapping)

        for feat in layer:
            try:

                # Freaky 3D geometries -- this seems harder than it should be.
                if layer.geom_type == 'POLYGON25D':
                    safe_geom = OGRGeometry(
                        self.remove_z(feat.geom.wkt), layer.srs)
                else:
                    safe_geom = feat.geom

                # force to multi
                # print(layer.srs)
                multipoly = OGRGeometry(OGRGeomType('MultiPolygon'), layer.srs)
                multipoly.add(safe_geom)

                # Translate to 4326, even if it probably already is.
                multipoly_4326 = multipoly.transform(4326, clone=True)
                # multipoly_utm = multipoly.transform(26915, clone=True)

                all_attributes = self.gather_all_attributes(layer.fields, feat)

                kwargs = {}
                for k, v in mapping.items():
                    # Check for static values
                    if type(v) is tuple:
                        kwargs[k] = v[1]
                    else:
                        kwargs[k] = all_attributes[v]
                # kwargs = {k: all_attributes[v] for k, v in mapping.items()}

                kwargs.update({
                    'workflow_id': workflow.id,
                    'feature_id': feat.fid,
                    'orig_data': all_attributes,
                    'orig_filename': orig_filename,
                    'geom_4326': multipoly_4326.wkt,
                    # 'geom_utm': multipoly_utm.wkt,
                })

                parcels.append(Parcel(**kwargs))
                parcel_count += 1

                if parcel_count % 10000 == 0:
                    Parcel.objects.bulk_create(parcels)
                    print('Saved {} parcel records...'.format(parcel_count))
                    parcels = []

            except GDALException as e:
                pass

        Parcel.objects.bulk_create(parcels)
        print('Saved {} records...'.format(parcel_count))

    def standardize_parcel_plats(self, workflow):
        ''' Standardize each unique addition name, and save back to Parcel objects with that plat_name'''
        print('Standardizing parcel plat names...')
        parcel_additions = Parcel.objects.filter(
            workflow=workflow).values_list('plat_name', flat=True).distinct()
        for pa in parcel_additions:
            print(pa)
            Parcel.objects.filter(workflow=workflow, plat_name=pa).update(
                plat_standardized=standardize_addition(pa))

    def join_to_plats(self, workflow):
        '''Find matching plat names based on addition value'''
        print("Joining plats to parcel objs...")
        plat_lookup = {p['plat_name_standardized']: p['id'] for p in Plat.objects.filter(
            workflow=workflow).values('id', 'plat_name_standardized')}
        plat_alternate_lookup = {p['alternate_name_standardized']: p['plat__id'] for p in PlatAlternateName.objects.filter(
            workflow=workflow).values('plat__id', 'alternate_name_standardized')}

        # Wait do we even need to do the alternate here or are we doing it twice?
        # TODO: Attempt plat match before trying to list all join options on both sides
        # plat match can be optional, but if it's there it can give you alternate candidates (again on both sides)

        # Merge alternates into main plat lookup
        plat_lookup.update(plat_alternate_lookup)

        plat_matches = []
        cant_match = {}
        for parcel in Parcel.objects.filter(workflow=workflow).only('plat_standardized', 'id'):
            try:
                plat_id = plat_lookup[parcel.plat_standardized]
                parcel.plat_id = plat_id
                plat_matches.append(parcel)
            except:
                if parcel.plat_standardized not in cant_match:
                    cant_match[parcel.plat_standardized] = 1
                else:
                    cant_match[parcel.plat_standardized] += 1

        print("Can't match these additions:")
        for plat, num_parcels in cant_match.items():
            print(f"{plat}: {num_parcels} parcels")

        print(f'\nUpdating {len(plat_matches)} Parcel objs...')
        Parcel.objects.bulk_update(plat_matches, ['plat_id'], batch_size=5000)

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

            for shp in self.batch_config['parcel_shps']:
                if 'download_url' in shp:
                    local_shp = self.download_shp(workflow, shp)
                elif 'local_shp' in shp:
                    # Check if unzip needed
                    if os.path.splitext(shp['local_shp'])[1] == '.zip':
                        local_shp = self.unzip_files(local_download_path, shp)
                    else:
                        local_shp = shp['local_shp']
                else:
                    print("No path to shapefile found. Exiting.")
                    raise

                print(
                    'Beginning homegrown layermapping: {} ...'.format(local_shp))
                self.save_parcels(workflow, local_shp, shp['mapping'])

            self.standardize_parcel_plats(workflow)
            self.join_to_plats(workflow)
            management.call_command(
                'rebuild_parcel_spatial_lookups', workflow=workflow_name)
