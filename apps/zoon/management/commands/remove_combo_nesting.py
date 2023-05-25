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

            # file_input = args.classification_export
            # file_output = args.output_file
            # combo_task_id = args.combo_task_id

            with open(file_output, 'w', newline='') as csvout:
                with open(file_input) as csvin:
                    classifications = csv.DictReader(csvin)
                    writer = csv.DictWriter(csvout, classifications.fieldnames)
                    writer.writeheader()
                    line_num = 0
                    for c in classifications:
                        # print(line_num)
                        line_num +=1
                        # print(c['annotations'])
                        annotations = json.loads(c['annotations'])
                        for a in annotations:
                            print(a)
                            if a['task'] in combo_task_ids:
                                # This is failing if different workflows have different combo tasks
                                try:
                                    for t in a['value']:
                                        annotations.append(t)
                                except:
                                    print("This doesn't appear to be a combo task. You might want to check that your list of combo tasks is correct for this workflow, or if you are using a classifications export that includes data from multiple workflows.")
                                    raise
                                annotations.remove(a)
                        c['annotations']=json.dumps(annotations)
                        writer.writerow(c)

# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description="Undo nesting of annotations for combo task")
#     parser.add_argument("--classification_export", required=True,
#                         help="Input Filename of Classification Export CSV")
#     parser.add_argument("--combo_task_id", required=True, help="Task ID for Combo Task")
#     parser.add_argument("--output_file", required=True, help="Output Filename for CSV")
#
#     args = parser.parse_args()
#     file_input = args.classification_export
#     file_output = args.output_file
#     combo_task_id = args.combo_task_id
#
#     with open(file_output, 'w', newline='') as csvout:
#         with open(file_input) as csvin:
#             classifications = csv.DictReader(csvin)
#             writer = csv.DictWriter(csvout, classifications.fieldnames)
#             writer.writeheader()
#             for c in classifications:
#                 annotations = json.loads(c['annotations'])
#                 for a in annotations:
#                     if a['task'] == combo_task_id:
#                         for t in a['value']:
#                             annotations.append(t)
#                         annotations.remove(a)
#                 c['annotations']=json.dumps(annotations)
#                 writer.writerow(c)
