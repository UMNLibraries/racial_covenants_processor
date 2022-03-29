import os
import re
import boto3

from django.core.management.base import BaseCommand
from django.conf import settings

from deeds.models import DeedPage
from zoon.models import ZooniverseWorkflow, ZooniverseSubject
from zoon.utils.zooniverse_config import get_workflow_version


class Command(BaseCommand):

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def get_workflow(self, workflow_name):
        self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]

        self.batch_dir = os.path.join(
            settings.BASE_DIR, 'data', 'zooniverse_exports', self.batch_config['panoptes_folder'])

        # Get workflow version from config yaml
        workflow_version = get_workflow_version(
            self.batch_dir, self.batch_config['config_yaml'])

        workflow = ZooniverseWorkflow.objects.get(
            workflow_name=workflow_name,
            version=workflow_version
        )
        return workflow

    def find_matching_keys(self, workflow):
        # Then use the session to get the resource
        s3 = self.session.resource('s3')

        my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

        key_filter = re.compile(f"web/{workflow.slug}/.+\.jpg")

        matching_keys = [obj.key for obj in my_bucket.objects.all(
        ) if re.match(key_filter, obj.key)]

        return matching_keys

    def build_django_objects(self, matching_keys, workflow):
        '''
        Parses the list of s3 keys from this workflow and creates Django DeedPage instances, saves them to the database

        Arguments:
            matching_keys: List of s3 keys matching our workflow
            workflow: Django ZooniverseWorkflow object
        '''
        deed_pages = []

        for mk in matching_keys:
            page_data = None
            try:
                page_data = re.search(
                    r'\/(?P<workflow_slug>[A-z\-]+)\/(?P<doc_num>\d+)_page_(?P<page_num>\d+)(?P<bool_match>_match)?', mk).groupdict()
                print(page_data)
            except:
                print(f'Could not parse image path data: {mk}')

            if page_data:
                # We aren't using the slug, so delete before model import
                del page_data['workflow_slug']

                # Set image path
                page_data['page_image_web'] = mk

                page_data['workflow_id'] = workflow.id

                # Re-code bool_match as boolean if found
                if page_data['bool_match']:
                    page_data['bool_match'] = True
                else:
                    page_data['bool_match'] = False

                deed_pages.append(DeedPage(
                    **page_data
                ))

        DeedPage.objects.bulk_create(deed_pages)

        return deed_pages

    def build_image_lookup(self, workflow):
        '''
        First step of join_to_subjects. Expands the list of image ids from the ZooniverseSubject instance to create a lookup table from each image id to the ZooniverseSubject primary key

        Arguments:
            workflow: Django ZooniverseWorkflow object
        '''

        subject_image_set = ZooniverseSubject.objects.filter(
            workflow=workflow
        ).exclude(
            image_ids__isnull=True
        ).values('id', 'image_ids')

        expanded_subject_image_set = {}
        for subject in subject_image_set:
            for image in subject['image_ids']:
                if image != '':
                    expanded_subject_image_set[image.replace(
                        '.png', '.jpg')] = subject['id']

        return expanded_subject_image_set

    def add_image_links(self, deed_pages, subject_image_lookup):
        '''
        Second step of join_to_subjects. Does the Django work to actually update the database

        Arguments:
            deed_pages: Django queryset of DeedPage objects from previously selected workflow
            subject_image_lookup: A dictionary where each key is an image id from the Zooniverse subject data, and the value is the pk value for the correct ZooniverseSubject instance
        '''

        # Build a lookup dict for the DeedImage objects for comparison to subject_image_lookup so we only loop through necessary DeedPage objects
        deed_pages_lookup = {os.path.basename(
            page['page_image_web']): page['id'] for page in deed_pages.values('id', 'page_image_web')}

        common_keys = [key for key in deed_pages_lookup.keys()
                       & subject_image_lookup.keys()]

        deed_pages_lookup_filtered = {
            key: deed_pages_lookup[key] for key in common_keys}

        pages_to_update = []
        for dp in deed_pages.filter(id__in=deed_pages_lookup_filtered.values()):
            dp.zooniverse_subject_id = subject_image_lookup[os.path.basename(
                str(dp.page_image_web))]
            pages_to_update.append(dp)

        print(f'Linking {len(pages_to_update)} images ...')
        DeedPage.objects.bulk_update(
            pages_to_update, ['zooniverse_subject_id'])

    def join_to_subjects(self, workflow):
        '''
        Joins DeedImage objects to the correct ZooniverseSubject, if found. Uses helper functions to generate lookups for efficient database updating.

        Arguments:
            workflow: Django ZooniverseWorkflow object
        '''
        deed_pages = DeedPage.objects.filter(
            workflow=workflow
            )

        subject_images = self.build_image_lookup(workflow)
        self.add_image_links(deed_pages, subject_images)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            DeedPage.objects.all().delete()

            workflow = self.get_workflow(workflow_name)

            matching_keys = self.find_matching_keys(workflow)

            image_objs = self.build_django_objects(
                matching_keys, workflow)

            self.join_to_subjects(workflow)
