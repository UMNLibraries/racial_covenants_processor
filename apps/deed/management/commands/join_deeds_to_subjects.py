import os
import boto3

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.deed.models import DeedPage
from apps.zoon.models import ZooniverseSubject
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):

    session = boto3.Session(
             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

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
        print('Linking DeedPage records to ZooniverseSubject records ...')


    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            deed_pages = DeedPage.objects.filter(
                workflow=workflow
                )

            subject_images = self.build_image_lookup(workflow)
            self.add_image_links(deed_pages, subject_images)
