import os
import csv
import json
# import argparse

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.zoon.utils.zooniverse_config import get_workflow_obj

class Command(BaseCommand):
    '''
    This is the remove_combo_nesting.py script from Zooniverse, ported to a Django management command.
    '''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "WI Milwaukee County"')

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']

        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
            return False
        else:
            workflow = get_workflow_obj(workflow_name)

            # This config info comes from local_settings, generally.
            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            self.batch_dir = os.path.join(
                settings.BASE_DIR, 'data', 'zooniverse_exports', self.batch_config['panoptes_folder'])

            file_input = os.path.join(
                self.batch_dir, f"{workflow.slug}-classifications.csv")

            file_output = os.path.join(
                self.batch_dir, f"{workflow.slug}-denested.csv")

            combo_task_ids = self.batch_config['zooniverse_config']['combo_task_ids']

            print(combo_task_ids)

            with open(file_output, 'w', newline='') as csvout:
                with open(file_input) as csvin:
                    classifications = csv.DictReader(csvin)
                    writer = csv.DictWriter(csvout, classifications.fieldnames)
                    writer.writeheader()
                    line_num = 0
                    for c in classifications:
                        line_num +=1
                        annotations = json.loads(c['annotations'])
                        out_annotations = []
                        for a in annotations:
                            if a['task'] in combo_task_ids:
                                # This is failing if different workflows have different combo tasks
                                try:
                                    for t in a['value']:
                                        out_annotations.append(t)
                                except:
                                    print("This doesn't appear to be a combo task. You might want to check that your list of combo tasks is correct for this workflow, or if you are using a classifications export that includes data from multiple workflows.")
                                    raise
                            else:
                                out_annotations.append(a)
                        c['annotations']=json.dumps(out_annotations)
                        writer.writerow(c)
