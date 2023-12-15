import os
import boto3

from django.core.management.base import BaseCommand
from django.conf import settings

from racial_covenants_processor.storage_backends import PrivateMediaStorage
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

    def build_hit_lookup(self, workflow):
        '''
        First step of join_to_subjects. Expands the list of image ids from the ZooniverseSubject instance to create a lookup table from each image id to the ZooniverseSubject primary key

        Arguments:
            workflow: Django ZooniverseWorkflow object
        '''

        subject_hit_set = ZooniverseSubject.objects.filter(
            workflow=workflow
        ).exclude(
            deedpage_s3_lookup__isnull=True
        ).values('id', 'deedpage_s3_lookup')

        subject_hit_lookup = {}
        for subject in subject_hit_set:
            subject_hit_lookup[subject['deedpage_s3_lookup']] = subject['id']

        return subject_hit_lookup

    def join_subjects_to_hits(self, deed_pages, subject_hit_lookup):
        '''
        Second step of join_to_subjects. Does the Django work to actually update the database

        Arguments:
            deed_pages: Django queryset of DeedPage objects from previously selected workflow
            subject_hit_lookup: A dictionary where each key is an s3_lookup from the Zooniverse subject data, and the value is the pk value for the correct ZooniverseSubject instance
        '''

        # Build a lookup dict for the DeedImage objects for comparison to subject_image_lookup so we only loop through necessary DeedPage objects
        deed_pages_lookup = {
            page['s3_lookup']: page['id'] for page in deed_pages.values('id', 's3_lookup')
        }

        common_keys = [key for key in deed_pages_lookup.keys()
                       & subject_hit_lookup.keys()]
        # common_keys = list(set(deed_pages_lookup.keys()).intersection(set(subject_hit_lookup.keys())))

        deed_pages_lookup_filtered = {
            key: deed_pages_lookup[key] for key in common_keys}

        pages_to_update = []
        for dp in deed_pages.filter(id__in=deed_pages_lookup_filtered.values()):
            dp.zooniverse_subject_id = subject_hit_lookup[dp.s3_lookup]
            pages_to_update.append(dp)

        print(f'Linking images for {len(pages_to_update)} hits ...')
        DeedPage.objects.bulk_update(
            pages_to_update, [f'zooniverse_subject'])

    def build_image_lookup(self, workflow, position):
        '''
        Third step of join_to_subjects. Expands the list of image ids from the ZooniverseSubject instance to create a lookup table from each image id to the ZooniverseSubject primary key

        Arguments:
            workflow: Django ZooniverseWorkflow object
        '''

        subject_image_set = ZooniverseSubject.objects.filter(
            workflow=workflow
        ).exclude(
            image_links__isnull=True
        ).values('id', 'image_links')

        expanded_subject_image_set = {}
        for subject in subject_image_set:
            image = subject['image_links'][position]
            # for image in subject['image_links']:
            if image not in ['', None]:
                expanded_subject_image_set[os.path.basename(image.replace(
                    '.png', '.jpg'))] = subject['id']

        return expanded_subject_image_set

    def add_image_links(self, deed_pages, subject_image_lookup, page):
        '''
        Fourth step of join_to_subjects. Does the Django work to actually update the database

        Arguments:
            deed_pages: Django queryset of DeedPage objects from previously selected workflow
            subject_image_lookup: A dictionary where each key is an image id from the Zooniverse subject data, and the value is the pk value for the correct ZooniverseSubject instance
            page: What position is this image in relative to the individual subject (1st, 2nd, or 3rd)
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
            setattr(
                dp,
                f'zooniverse_subject_{page}_page_id',
                subject_image_lookup[os.path.basename(str(dp.page_image_web))]
            )
            pages_to_update.append(dp)

        print(f'{page} page: Linking {len(pages_to_update)} images ...')
        DeedPage.objects.bulk_update(
            pages_to_update, [f'zooniverse_subject_{page}_page'])

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            deed_pages = DeedPage.objects.filter(
                workflow=workflow
            ).only('id', 'page_image_web', 's3_lookup')

            # Join to deed page of hit via deedpage_s3_lookup
            subject_hit_lookup = self.build_hit_lookup(workflow)
            self.join_subjects_to_hits(deed_pages, subject_hit_lookup)


            # Join all related DeedPage images based on image position
            subject_images_1st = self.build_image_lookup(workflow, 0)
            subject_images_2nd = self.build_image_lookup(workflow, 1)
            subject_images_3rd = self.build_image_lookup(workflow, 2)

            self.add_image_links(deed_pages, subject_images_1st, '1st')
            self.add_image_links(deed_pages, subject_images_2nd, '2nd')
            self.add_image_links(deed_pages, subject_images_3rd, '3rd')
