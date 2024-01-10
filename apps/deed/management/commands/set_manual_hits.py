import os
import pandas as pd

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.deed.models import DeedPage
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Use a CSV to manually set hits or exceptions on DeedPage objects before uploading to Zooniverse
    Created to reconcile two batches from same county.
    
    Matching to DeedPage records requires a lookup by s3_lookup, so if the s3_lookup has changed between batches
    you will need to do some manual pre-processing of your CSV so you find the correct DeedPages in your current workflow.
    '''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

        parser.add_argument('-f', '--file', type=str,
                            help='Path to CSV containing hits/exceptions')


    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        csv_path = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
            return False
        else:
            workflow = get_workflow_obj(workflow_name)

        if not csv_path:
            print('Missing CSV file path. Please specify with --file.')
            return False
        
        if not os.path.isfile(csv_path):
            print('CSV file path is not valid. Please specify with --file.')
            return False
        
        hit_df = pd.read_csv(csv_path)
        manual_hits_df = df[df['bool_hit'] == True]
        manual_exceptions_df = df[df['bool_exception'] == True]

        # DeedPage.objects.filter(
        #     workflow=workflow,
        #     s3_lookup__in=manual_hits_df.s3_lookup.to_list()
        # ).update(
        #     bool_match=True,
        #     bool_exception=False,
        #     bool_manual=True
        # )

        # DeedPage.objects.filter(
        #     workflow=workflow,
        #     s3_lookup__in=manual_exceptions_df.s3_lookup.to_list()
        # ).update(
        #     bool_match=False,
        #     bool_exception=True,
        #     bool_manual=True
        # )
