import pandas as pd

import panoptes_client
from panoptes_client import Panoptes, Project, Subject, SubjectSet

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.zoon.utils.zooniverse_load import build_zooniverse_manifest
from apps.deed.models import DeedPage


class Command(BaseCommand):
    '''This uploader is based heavily on a custom Zooniverse uploader built by Peter Mason.

    It builds multiframe image subjects with the metadata a unique identifier from the first column and
    the remote locations hosting the images in a variable number of additional columns.
    Subjects are uploaded to a specified subject set that exists or is created
    in the project. The script reports errors that occurred and is restartable
    without subject duplication. Optionally a summary file of all subjects
    successfully uploaded can be produced and saved.
    To connect to panoptes the zooniverse user_name and password must be stored
    in the users operating system environmental variables USERNAME and PASSWORD.
    If this is not the case line 96 must be modified to the form
    Panoptes.connect(username='jmschell', password='actual-password'), and
    steps must be taken to protect this script.
    NOTE: You may use a file to hold the command-line arguments like:
    @/path/to/args.txt.
    '''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "WI Milwaukee County"')

        parser.add_argument('-n', '--num_subjects', type=int,
                            help='Number of subjects to upload')

    def connect_to_zooniverse(self):
        Panoptes.connect(username=settings.ZOONIVERSE_USERNAME, password=settings.ZOONIVERSE_PASSWORD)
        project = Project.find(slug='mappingprejudice/mapping-prejudice')

        return project

    def get_or_create_subject_set(self, project, workflow):
        try:
            subject_set = SubjectSet.where(project_id=project.id, display_name=workflow.workflow_name).next()
            print(f"Found existing subjet set {workflow.workflow_name} ({subject_set.id}).")

        except StopIteration:
            print(f"No matching subject set found. Creating '{workflow.workflow_name}'...")
            subject_set = SubjectSet()
            subject_set.links.project = project
            subject_set.display_name = workflow.workflow_name
            subject_set.save()
            print(f"Subject set {subject_set.id} created.")
        return subject_set

    def get_existing_subjects(self, subject_set):
        print("Getting existing subjects in subject set...")
        return [subject.metadata['#s3_lookup'] for subject in subject_set.subjects]

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        num_subjects = kwargs['num_subjects']

        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
            return False
        else:
            workflow = get_workflow_obj(workflow_name)

        if not kwargs['num_subjects']:
            print("Missing number of subjects. Please specify with -n or --num_subjects.")
            return False
        else:

            zooniverse_project = self.connect_to_zooniverse()
            subject_set = self.get_or_create_subject_set(zooniverse_project, workflow)

            existing_subject_ids = self.get_existing_subjects(subject_set)

            print(f"Found {len(existing_subject_ids)} existing subjects. Building manifest...")

            upload_manifest = build_zooniverse_manifest(workflow, existing_subject_ids, num_subjects)
            columns = upload_manifest.columns

            for index, row in upload_manifest.iterrows():
                try:
                    subject = Subject()
                    subject.links.project = zooniverse_project

                    for image_col in ['#image1', '#image2', '#image3']:
                        if row[image_col] != '':
                            subject.add_location({'image/jpeg': row[image_col]})

                    subject.metadata.update(row)
                    subject.save()
                    subject_set.add(subject.id)

                    print('{} successfully uploaded'.format(row['pk']))
                except panoptes_client.panoptes.PanoptesAPIException:
                    raise
                    print('An error occurred during the upload of {}'.format(row['pk']) + '\n')
