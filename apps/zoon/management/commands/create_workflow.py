import os
import re
import json
import datetime
import pandas as pd
from itertools import chain
from sqlalchemy import create_engine

from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings

from apps.zoon.models import ZooniverseResponseRaw, ZooniverseWorkflow
from apps.zoon.utils.zooniverse_config import get_workflow_version


class Command(BaseCommand):
    '''This is the main loader for a Zooniverse export and set of reduced output into the Django app.'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def create_workflow(self, workflow_zoon_id: str, workflow_name: str, workflow_version: str):

        workflow, w_created = ZooniverseWorkflow.objects.get_or_create(
            zoon_id=workflow_zoon_id,
            workflow_name=workflow_name,
            version=workflow_version
        )
        if w_created:
            print(f"New workflow record created for {workflow_name}.")
        else:
            print(f"Existing workflow record found for {workflow_name}.")
        return workflow

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            # This config info comes from local_settings, generally.
            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            workflow_slug = workflow_name.lower().replace(" ", "-")

            if 'panoptes_folder' in self.batch_config:
                self.batch_dir = os.path.join(
                    settings.BASE_DIR, 'data', 'zooniverse_exports', self.batch_config['panoptes_folder'])

                # Get workflow version from config yaml, or set to None for now
                workflow_version = get_workflow_version(
                    self.batch_dir, self.batch_config['config_yaml'])
            else:
                workflow_version = None

            if 'zoon_workflow_id' in self.batch_config:
                workflow_zoon_id = self.batch_config['zoon_workflow_id']
            else:
                workflow_zoon_id = None

            workflow = self.create_workflow(
                workflow_zoon_id,
                workflow_name,
                workflow_version
            )
