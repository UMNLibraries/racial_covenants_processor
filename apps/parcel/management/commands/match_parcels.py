import os
import csv
import sys
import datetime
from io import StringIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.zoon.models import ZooniverseSubject
from apps.parcel.models import JoinReport
from apps.parcel.utils.parcel_utils import build_parcel_spatial_lookups
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Attempt to auto-join covenants to modern parcels using current values'''
    matched_lots = []
    match_report = []

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        parser.add_argument('-l', '--local', action='store_true',
                            help='Save to local CSV in "analysis" dir, rather than Django object/S3')

    def match_parcel(self, parcel_lookup, target_obj, subject_obj):
        ''' Separate subject necessary because you also have to run this on the ExtraParcelCandidate objects and then link the result to its subject'''
        # candidates = get_covenant_parcel_options(target_obj)
        candidates = target_obj.join_candidates
        for c in candidates:
            try:
                lot_match = parcel_lookup[c['join_string']]


                c['match'] = True
                c['parcel_metadata'] = lot_match['parcel_metadata']
                c['num_parcels'] = len(lot_match['parcel_ids'])

                print(f"MATCH: {c['join_string']} ({c['num_parcels']} parcels)")

                for parcel_id in lot_match['parcel_ids']:
                    subject_obj.parcel_matches.add(parcel_id)
                self.matched_lots.append(c)

            except KeyError as e:
                print(f"NO MATCH: {c['join_string']}")
                c['match'] = False
                c['num_parcels'] = 0
            self.match_report.append(c)

    def match_parcels_bulk(self, workflow, parcel_lookup):
        print("Attempting to auto-join covenants to parcels ...")
        for covenant in ZooniverseSubject.objects.filter(
            workflow=workflow,
            bool_covenant_final=True
        ).order_by('addition_final'):
            self.match_parcel(parcel_lookup, covenant, covenant)

        matched_qs = ZooniverseSubject.objects.filter(
            pk__in=[c['subject_id'] for c in self.matched_lots])

        # Update boolean for subjects with matching parcels in bulk
        matched_qs.update(bool_parcel_match=True)

        # Update geo union fields for final export
        update_objs = []
        for z in matched_qs:
            z.set_geom_union()
            z.set_addresses()
            update_objs.append(z)
        ZooniverseSubject.objects.bulk_update(
            update_objs, ['geom_union_4326', 'parcel_addresses', 'parcel_city'], batch_size=1000)

    def write_match_report(self, workflow, bool_local=False):
        fieldnames = ['join_string', 'match', 'subject_id',
                      'metadata', 'parcel_metadata', 'num_parcels']

        now = datetime.datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%m')

        matched_lots = [s for s in self.match_report if s['match'] is True]
        matched_subjects = set([s['subject_id'] for s in matched_lots])

        covenant_count = ZooniverseSubject.objects.filter(
            workflow=workflow,
            bool_covenant_final=True
        ).count()

        matched_lot_count = len(matched_lots)
        matched_subject_count = len(matched_subjects)

        print(f"{covenant_count} covenant subjects")
        print(
            f"{matched_lot_count} lot matches found on {matched_subject_count} subjects.")

        filename_tail = f'{workflow.slug}_match_report_{timestamp}.csv'

        if bool_local:

            outfile_path = os.path.join(
                settings.BASE_DIR, 'data', 'analysis', filename_tail)
            print(f'Writing report to {outfile_path}')
            with(open(outfile_path, 'w') as outfile):
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writerows(self.match_report)
        else:
            print('Creating JoinReport object...')
            # writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            # writer.writerows(self.match_report)

            csv_buffer = StringIO()
            csv_writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            csv_writer.writeheader()
            csv_writer.writerows(self.match_report)

            csv_file = ContentFile(csv_buffer.getvalue().encode('utf-8'))

            report_obj = JoinReport(
                workflow=workflow,
                # report_csv=csv_file,
                covenant_count=covenant_count,
                matched_lot_count=matched_lot_count,
                matched_subject_count=matched_subject_count,
                created_at=now
            )
            report_obj.report_csv.save(filename_tail, csv_file)
            report_obj.save()

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            # Get all possible parcel lots to join
            parcel_lookup = build_parcel_spatial_lookups(workflow)
            self.match_parcels_bulk(workflow, parcel_lookup)

            bool_local = kwargs['local']
            self.write_match_report(workflow, bool_local)
