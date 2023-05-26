import os
import json
import pandas as pd
import subprocess

from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings

from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''This runs a series of panoptes aggregation commands, a bit crudely.'''
    batch_config = None  # Set in handle
    batch_dir = None
    zoon_workflow_id = None
    zoon_workflow_version = None
    config_yaml = None
    workflow = None
    workflow_csv_path = None

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def run_extractor(self, extractor="text"):
        print(f"Starting {extractor} reducer...")
        extractor_yaml = os.path.join(self.batch_dir,
            f"Reducer_config_workflow_{self.zoon_workflow_id}_V{self.zoon_workflow_version}_{extractor}_extractor.yaml")
        extractions_csv = os.path.join(self.batch_dir, f"{extractor}_extractor_extractions.csv")

        process = subprocess.run(['panoptes_aggregation', 'reduce', '-d', self.batch_dir, '-o', self.workflow.slug, extractions_csv, extractor_yaml])

    def generate_task_2_question_lookup(self):
        '''It's sometimes hard to parse out which task goes with one question, so this produces a somewhat more readable list of what question goes with each task. This can be used to facilitate filling out the zooniverse config for each workflow.'''
        workflow_df = pd.read_csv(self.workflow_csv_path)
        workflow_df['full_version'] = workflow_df["version"].astype('str').str.cat(workflow_df[["minor_version"]].astype(str), sep=".")

        current_workflow_df = workflow_df[
            (workflow_df['workflow_id'] == int(self.zoon_workflow_id))
            & (workflow_df['full_version'] == self.zoon_workflow_version)
        ]
        # Some type of question labels are in the "strings" fields
        strings = json.loads(current_workflow_df.iloc[0].strings)
        questions = {k: v for k, v in dict(strings).items() if '.question' in k or '.instruction' in k}

        tasks = json.loads(current_workflow_df.iloc[0].tasks)
        q_text = 'GUIDE TO WORKFLOW QUESTIONS\n\n'
        for k, v in tasks.items():
            q_text += f'Task: {k}\n'
            if 'question' in v:
                question = questions[v['question']]
                q_text += question + '\n\n'

            elif v['type'] == 'dropdown':
                q_text += f"DROPDOWN {v['selects'][0]['title']}\n\n"

            elif 'instruction' in v:
                question = questions[v['instruction']]
                q_text += question + '\n\n'

            elif v['type'] == 'combo':
                q_text += f"COMBO of {','.join(v['tasks'])}\n\n"

        return q_text

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            self.workflow = get_workflow_obj(workflow_name)

            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]

            self.batch_dir = os.path.join(
                settings.BASE_DIR, 'data', 'zooniverse_exports', self.batch_config['panoptes_folder'])

            self.zoon_workflow_id = str(self.batch_config['zoon_workflow_id'])
            # self.zoon_workflow_version = str(self.batch_config['zoon_workflow_version'])
            self.zoon_workflow_version = "{:.2f}".format(self.batch_config['zoon_workflow_version'])

            self.workflow_csv_path = os.path.join(
                self.batch_dir, f"{self.workflow.slug}-workflows.csv")

            process = subprocess.run(['panoptes_aggregation', 'config', '-v', self.zoon_workflow_version, '-d', self.batch_dir, self.workflow_csv_path, self.zoon_workflow_id])

            # De-nest annotations for combo questions
            management.call_command(
                'remove_combo_nesting', workflow=workflow_name)

            self.config_yaml = os.path.join(
                self.batch_dir, f"Extractor_config_workflow_{self.zoon_workflow_id}_V{self.zoon_workflow_version}.yaml")
            self.denested_class_path = os.path.join(
                self.batch_dir, f"{self.workflow.slug}-denested.csv")

            # Aggregation extract - specific numbers may change with workflow updates
            process = subprocess.run(['panoptes_aggregation', 'extract', '-d', self.batch_dir, self.denested_class_path, self.config_yaml])

            self.run_extractor("text")
            self.run_extractor("question")
            self.run_extractor("dropdown")

            task_lookup = self.generate_task_2_question_lookup()
            print('\n\n' + task_lookup)
