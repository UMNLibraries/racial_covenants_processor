# import os
# import ast
# import json
import pandas as pd
# from sqlalchemy import create_engine

from django.core.management.base import BaseCommand
from django.conf import settings

# from apps.zoon.utils.zooniverse_config import parse_config_yaml
from apps.zoon.utils.zooniverse_config import get_workflow_obj

# import argparse
# import textwrap
# import csv
# import os
# import io
# import validators
# from datetime import datetime
# import panoptes_client
from panoptes_client import Panoptes, Project, Subject, SubjectSet


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

    def connect_to_zooniverse(self):
        Panoptes.connect(username=settings.ZOONIVERSE_USERNAME, password=settings.ZOONIVERSE_PASSWORD)
        project = Project.find(slug='mappingprejudice/mapping-prejudice')

        return project

    def get_or_create_subject_set(self, project, workflow):
        try:
            subject_set = SubjectSet.where(project_id=project.id, display_name=workflow.workflow_name).next()
            print(f"Found existing subjet set {workflow.workflow_name} ({subject_set.id}).")

        except StopIteration:
        #     # create a new subject set link it to the project above
        #     build_part += 'You have chosen to upload {} subjects to a new subject set {}'.format(total_rows, set_name) + '\n'
        #     print(build_part)
        #     retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
        #     if retry.lower() == 'n':
        #         quit()
        #     if save:
        #         build_file += build_part
        #     # nothing happens until the subject_set.save(). For testing comment out that line
            print(f"No matching subject set found. Creating '{workflow.workflow_name}'...")
            subject_set = SubjectSet()
            subject_set.links.project = project
            subject_set.display_name = workflow.workflow_name
            subject_set.save()
            print(f"Subject set {subject_set.id} created.")
        return subject_set

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            zooniverse_project = self.connect_to_zooniverse()
            subject_set = self.get_or_create_subject_set(zooniverse_project, workflow)


# # where the optional summary is output:
# def output(location, build):
#     with io.open(location, 'w', encoding='utf-8', newline='') as out_file:
#         out_file.write(build)
#     return
#
#
# parser = argparse.ArgumentParser(
#     formatter_class=argparse.RawDescriptionHelpFormatter,
#     fromfile_prefix_chars='@',
#     description=textwrap.dedent("""
#             This script is an uploader customized for Justin Schell.
#             It requires a manifest in a specific format. It builds multiframe image
#             subjects with the metadata a unique identifier from the first column and
#             the remote locations hosting the images in a variable number of additional columns.
#             Subjects are uploaded to a specified subject set that exists or is created
#             in the project. The script reports errors that occurred and is restartable
#             without subject duplication. Optionally a summary file of all subjects
#             successfully uploaded can be produced and saved.
#             To connect to panoptes the zooniverse user_name and password must be stored
#             in the users operating system environmental variables USERNAME and PASSWORD.
#             If this is not the case line 96 must be modified to the form
#             Panoptes.connect(username='jmschell', password='actual-password'), and
#             steps must be taken to protect this script.
#             NOTE: You may use a file to hold the command-line arguments like:
#             @/path/to/args.txt."""))
#
# parser.add_argument('--manifest', '-m', required=True,
#                     help="""The manifest is required. It must a unique identifier in
#                     the very first column column and the remote hppts locations hosting
#                     the images in a variable number of additional columns.
#                     Give the full path (from the
#                     directory where this script is run, or from the root directory) and
#                     the file name. The manifest must be a csv file using commas as the
#                     delimiter.
#                     example -m C:\py\TBD\FISHc_Pages_Standard_Manifest.csv""")
# parser.add_argument('--subject_set', '-s', required=False, default='New subject set',
#                     help="""The name of the subject set to create for or to add the uploaded
#                     subjects to. This argument is optional and defaults to "New subject set".
#                     This name can be edited via the project builder. If the script is being
#                     restarted with the intention of adding more subjects to an existing set,
#                     the subject_set name must be exactly the same.
#                     example -s "A different set" (note quotes)  """)
# parser.add_argument('--save_to', '-f', required=False, default='None',
#                     help="""An optional file name (including extension ".csv"
#                     where the summary of the subjects uploaded will be saved in csv format.
#                     Give the full path (from the directory where this script is run, or from the
#                     root directory) and the file name.
#                     example -f some_path\summary_file.csv """)
# args = parser.parse_args()
#
# manifest = args.manifest
# set_name = args.subject_set
# save_to = args.save_to
#
# save = False
# if '.csv' in save_to:
#     save = True
#
# # parts of the optional summary file are built and either printed or added to the summary file
# build_file = ''
# build_part = "Subject uploader for project 'FISHc_Pages'" + '\n'
# build_part += "Manifest = {}   Subject_Set Name = {}   Save location = {}" \
#                   .format(manifest, set_name, save_to) + '\n' + '\n'
#
# build_part += 'Loading manifest:' + '\n'
# with open(manifest, 'r') as m_file:
#     r = csv.DictReader(m_file)
#     manifest_header = r.fieldnames
#     manifest_list = []
#     total_rows = 0
#     for row in r:
#         manifest_line = {manifest_header[0]: row[manifest_header[0]]}
#         for i in range(1, len(row)):
#             if row[manifest_header[i]]:
#                 manifest_line[manifest_header[i]] = row[manifest_header[i]]
#
#         manifest_list.append(manifest_line)
#         total_rows += 1
#     build_part += '\n'
#
# # connection and login for the project:
# Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
# project = Project.find(slug='jmschell/angling-for-data-on-michigan-fishes')  # TODO This may need to be changed!
# # project = Project.find(slug='pmason/fossiltrainer')
#
# #  This section sets up a subject set
# previous_subjects = []
# try:
#     # check if the subject set already exits
#     subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
#     build_part += 'You have chosen to upload {} subjects to an existing subject set {}'.format(total_rows, set_name) \
#                   + '\n'
#     print(build_part)
#     retry = input('Enter "n" to cancel this upload, any other key to continue;' + '\n')
#     if retry.lower() == 'n':
#         quit()
#     if save:
#         build_file += build_part
#     # get listing of previously uploaded subjects
#     print('Please wait while the existing subjects are determined, this can take approximately one minute per '
#           '400 previous subjects depending on the connection speed and zooinverse workload')
#     for subject in subject_set.subjects:
#         previous_subjects.append(subject.metadata[manifest_header[0]])
#     build_part = '{} subjects found in this set'.format(len(previous_subjects)) + '\n'
#     print(build_part)
#     if save:
#         build_file += build_part
# except StopIteration:
#     # create a new subject set link it to the project above
#     build_part += 'You have chosen to upload {} subjects to a new subject set {}'.format(total_rows, set_name) + '\n'
#     print(build_part)
#     retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
#     if retry.lower() == 'n':
#         quit()
#     if save:
#         build_file += build_part
#     # nothing happens until the subject_set.save(). For testing comment out that line
#     subject_set = SubjectSet()
#     subject_set.links.project = project
#     subject_set.display_name = set_name
#     subject_set.save()
#
# print('Uploading subjects, This could take a while!')
# new_subjects = 0
# old_subjects = 0
# failed_subjects = 0
# working_on = []
# #  loop over the preloaded manifest file
# for metadata in manifest_list:
#     working_on = metadata[manifest_header[0]]
#     build_part = 'working on {}'.format(working_on) + '\n'
#     #  test for previously uploaded
#     if metadata[manifest_header[0]] not in previous_subjects:
#         try:
#             subject = Subject()
#             subject.links.project = project
#             #  find the files in the metadata and add their locations
#             for field in list(metadata.keys())[1:]:
#                 if validators.url(metadata[field]):
#                     subject.add_location({'image/jpeg': metadata[field]})
#             # update subject metadata
#             subject.metadata.update(metadata)
#             build_part += str(metadata) + '\n'
#             # again nothing happens until these two lines below, comment them out for testing  # TODO !!!!!!!!!
#             # subject.save()
#             # subject_set.add(subject.id)
#             new_subjects += 1
#             build_part += '{} successfully uploaded at {}'.format(working_on, str(datetime.now())[0:19]) + '\n'
#         except panoptes_client.panoptes.PanoptesAPIException:
#             failed_subjects += 1
#             build_part += 'An error occurred during the upload of {}'.format(working_on) + '\n'
#     else:
#         old_subjects += 1
#         build_part += '{} previously uploaded'.format(working_on) + '\n'
#     print(build_part, end='')
#     if save:
#         build_file += build_part
#
# build_part = '\n' + '\n' + '\n' + 'Of {} subjects listed in the manifest -'.format(total_rows) + '\n'
# build_part += '{} new subjects were created and uploaded'.format(new_subjects) + '\n'
# build_part += '{} subjects were already uploaded and {} subjects failed to upload' \
#                   .format(old_subjects, failed_subjects) + '\n'
#
# print(build_part)
# if save:
#     build_file += build_part
# #  test for the optional summary output
# if save:
#     output(save_to, build_file)
# #  ____________________________________________________________________________________________________________________
