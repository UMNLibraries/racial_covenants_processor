import os
import csv
import sys
import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.parcel.utils.parcel_utils import build_parcel_spatial_lookups
from apps.zoon.models import ZooniverseSubject
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Attempt to auto-join covenants to modern parcels using current values'''
    batch_config = None  # Set in handle
    matched_lots = []
    match_report = []

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def match_parcel(self, parcel_lookup, target_obj, subject_obj):
        ''' Separate subject necessary because you also have to run this on the ExtraParcelCandidate objects and then link the result to its subject'''
        # candidates = get_covenant_parcel_options(target_obj)
        candidates = target_obj.join_candidates
        for c in candidates:
            try:
                lot_match = parcel_lookup[c['join_string']]
                print(f"MATCH: {c['join_string']}")

                c['match'] = True
                c['parcel_metadata'] = lot_match['parcel_metadata']

                subject_obj.parcel_matches.add(lot_match['parcel_id'])
                self.matched_lots.append(c)

            except KeyError as e:
                print(f"NO MATCH: {c['join_string']}")
                c['match'] = False
            self.match_report.append(c)

    def match_parcels_bulk(self, workflow, parcel_lookup):
        print("Attempting to auto-join covenants to parcels ...")
        for covenant in ZooniverseSubject.objects.filter(
            workflow=workflow,
            bool_covenant_final=True
        ).order_by('addition_final'):
            self.match_parcel(parcel_lookup, covenant, covenant)

        # print('Attempting to auto-join extra parcel candidates...')
        # for extra_parcel in ExtraParcelCandidate.objects.all():
        #     self.match_parcel(parcel_lookup, extra_parcel,
        #                       extra_parcel.zooniverse_subject)

        matched_qs = ZooniverseSubject.objects.filter(
            pk__in=[c['subject_id'] for c in self.matched_lots])
        # Update boolean for subjects with matching parcels in bulk
        matched_qs.update(bool_parcel_match=True)

        # Update geo union fields for final export
        update_objs = []
        for z in matched_qs:
            z.set_geom_union()
            update_objs.append(z)
        ZooniverseSubject.objects.bulk_update(
            update_objs, ['geom_union_4326'], batch_size=1000)

    def write_match_report(self, workflow, bool_file=True):
        fieldnames = ['join_string', 'match', 'subject_id',
                      'metadata', 'parcel_metadata']

        if bool_file:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%m')
            outfile_path = os.path.join(
                settings.BASE_DIR, 'data', 'analysis', f'{workflow.slug}_match_report_{timestamp}.csv')
            print(f'Writing report to {outfile_path}')
            with(open(outfile_path, 'w') as outfile):
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writerows(self.match_report)
        else:
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writerows(self.match_report)

        cov_count = ZooniverseSubject.objects.filter(
            workflow=workflow,
            bool_covenant_final=True
        ).count()

        print(f"{cov_count} covenant subjects")

        # print(self.match_report)

        matched_lots = [s for s in self.match_report if s['match'] is True]
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
            workflow = get_workflow_obj(workflow_name)

            # Get all possible parcel lots to join
            parcel_lookup = build_parcel_spatial_lookups(workflow)
            self.match_parcels_bulk(workflow, parcel_lookup)
            self.write_match_report(workflow)
