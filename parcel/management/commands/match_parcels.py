import re
import os
import csv
import sys
import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

from parcel.models import Parcel
from parcel.utils.parcel_utils import get_covenant_parcel_options, get_all_parcel_options, build_parcel_spatial_lookups
from zoon.models import ZooniverseWorkflow, ZooniverseSubject
from zoon.utils.zooniverse_config import get_workflow_version


class Command(BaseCommand):
    '''Attempt to auto-join covenants to modern parcels using current values'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def match_parcels_bulk(self, workflow, parcel_lookup):
        print("Attempting to auto-join covenants to parcels ...")
        matched_subjects = []
        match_report = []
        for covenant in ZooniverseSubject.objects.filter(
            workflow=workflow,
            bool_covenant_final=True
        ).order_by('addition_final'):
            candidates, metadata = get_covenant_parcel_options(covenant)
            for c in candidates:
                try:
                    lot_match = parcel_lookup[c['join_string']]
                    print(f"MATCH: {c['join_string']}")
                    matched_subjects.append(c)

                    c['match'] = True
                    c['parcel_metadata'] = lot_match['parcel_metadata']
                except:
                    print(f"NO MATCH: {c['join_string']}")
                    c['match'] = False
                match_report.append(c)

        self.write_match_report(workflow, match_report)

    def write_match_report(self, workflow, report_list, bool_file=True):
        fieldnames = ['join_string', 'match', 'subject_id',
                      'covenant_metadata', 'parcel_metadata']

        if bool_file:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%m')
            outfile_path = os.path.join(
                settings.BASE_DIR, 'data', 'analysis', f'{workflow.slug}_match_report_{timestamp}.csv')
            print(f'Writing report to {outfile_path}')
            with(open(outfile_path, 'w') as outfile):
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writerows(report_list)
        else:
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writerows(report_list)

        cov_count = ZooniverseSubject.objects.filter(
            workflow=workflow,
            bool_covenant_final=True
        ).count()

        print(f"{cov_count} covenant subjects")

        matched_lots = [s for s in report_list if s['match'] is True]
        matched_subjects = set([s['subject_id'] for s in matched_lots])

        print(
            f"{len(matched_lots)} lot matches found on {len(matched_subjects)} subjects.")

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            # This config info comes from local_settings, generally.
            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            self.batch_dir = os.path.join(
                settings.BASE_DIR, 'data', 'zooniverse_exports', self.batch_config['panoptes_folder'])

            # Get workflow version from config yaml
            workflow_version = get_workflow_version(
                self.batch_dir, self.batch_config['config_yaml'])

            workflow = ZooniverseWorkflow.objects.get(
                workflow_name=workflow_name, version=workflow_version)

            # Find all possible parcel lots to join
            parcel_lookup = build_parcel_spatial_lookups(workflow)

            self.match_parcels_bulk(workflow, parcel_lookup)
