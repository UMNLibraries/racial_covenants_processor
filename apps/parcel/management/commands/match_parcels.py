import os
import csv
import sys
import datetime
from io import StringIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.zoon.models import ZooniverseSubject, ManualCovenant, ManualParcelPINLink, ManualCovenantParcelPINLink
from apps.parcel.models import JoinReport, Parcel, CovenantedParcel
from apps.parcel.utils.parcel_utils import build_parcel_spatial_lookups, addition_wide_parcel_match
from apps.parcel.utils.export_utils import delete_flat_covenanted_parcels, save_flat_covenanted_parcels
from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.zoon.utils.zooniverse_join import set_addresses


class Command(BaseCommand):
    '''Attempt to auto-join covenants to modern parcels using current values'''
    matched_lots_zoon = []
    matched_lots_manual = []
    match_report = []

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        parser.add_argument('-l', '--local', action='store_true',
                            help='Save to local CSV in "analysis" dir, rather than Django object/S3')
        parser.add_argument('-t', '--test', action='store_true',
                            help="Don't save match report, this is only a test")

    def match_parcel(self, parcel_lookup, target_obj, subject_obj, matched_lots_list):
        ''' Separate subject necessary because you also have to run this on the ExtraParcelCandidate objects and then link the result to its subject'''
        # candidates = get_covenant_parcel_options(target_obj)
        candidates = target_obj.join_candidates
        for c in candidates:
            try:
                lot_match = parcel_lookup[c['join_string']]

                c['match'] = True
                c['parcel_metadata'] = lot_match['parcel_metadata']
                c['parcel_metadata']['parcel_ids'] = lot_match['parcel_ids']
                c['num_parcels'] = len(lot_match['parcel_ids'])

                print(f"MATCH: {c['join_string']} ({c['num_parcels']} parcels)")

                for parcel_id in lot_match['parcel_ids']:
                    subject_obj.parcel_matches.add(parcel_id)
                matched_lots_list.append(c)

            except KeyError as e:
                print(f"NO MATCH: {c['join_string']}")
                c['match'] = False
                c['num_parcels'] = 0
            self.match_report.append(c)

    def match_parcels_bulk_zoon(self, workflow, parcel_lookup):
        print("Attempting to auto-join zooniverse covenants to parcels ...")
        for covenant in ZooniverseSubject.objects.filter(
            workflow=workflow,
            bool_covenant_final=True
        ).exclude(
            addition_final=''
        ).exclude(
            match_type_final='AW'  # Addition-wide covenants handled later
        ).order_by('addition_final'):
            self.match_parcel(parcel_lookup, covenant, covenant, self.matched_lots_zoon)

        matched_qs = ZooniverseSubject.objects.filter(
            pk__in=[c['subject_id'] for c in self.matched_lots_zoon])

        # Update boolean for subjects with matching parcels in bulk
        matched_qs.update(bool_parcel_match=True)

        # Update geo union fields for final export
        update_objs = []
        for z in matched_qs:
            z.set_geom_union()
            set_addresses(z)
            update_objs.append(z)
        ZooniverseSubject.objects.bulk_update(
            update_objs, ['geom_union_4326', 'parcel_addresses', 'parcel_city'], batch_size=1000)
        
    def match_parcels_bulk_manual(self, workflow, parcel_lookup):  # TODO: Same for ManualCovenant objects

        print("Attempting to auto-join manual covenants to parcels ...")
        for covenant in ManualCovenant.objects.filter(
            workflow=workflow,
            bool_confirmed=True
        ).exclude(
            cov_type='PT'  # Addition-wide covenants handled later TODO
        ).order_by('addition'):
            self.match_parcel(parcel_lookup, covenant, covenant, self.matched_lots_manual)

        matched_qs = ManualCovenant.objects.filter(
            pk__in=[c['subject_id'] for c in self.matched_lots_manual])

        # Update boolean for subjects with matching parcels in bulk
        matched_qs.update(bool_parcel_match=True)

        # Update geo union fields for final export
        update_objs = []
        for m in matched_qs:
            set_addresses(m)
            update_objs.append(m)
        ManualCovenant.objects.bulk_update(
            update_objs, ['parcel_addresses', 'parcel_city'], batch_size=1000)

    def tag_matched_parcels(self, workflow):
        # Clear previous bool_covenant values on workflow
        print("Clearing old bool_covenant values from Parcels in this workflow...")
        Parcel.objects.filter(workflow=workflow, bool_covenant=True).update(bool_covenant=False)

        print("Tagging bool_covenant=True for matched Parcels on ZooniverseSubjects...")
        Parcel.objects.filter(workflow=workflow, zooniversesubject__isnull=False, zooniversesubject__bool_covenant_final=True).update(bool_covenant=True)

        print("Tagging bool_covenant=True for matched Parcels on ManualCovenants...")
        Parcel.objects.filter(workflow=workflow, manualcovenant__isnull=False, manualcovenant__bool_confirmed=True).update(bool_covenant=True)

    def save_flattened_covenants(self, workflow):
        # Do a more broad deletion to find any stragglers
        print("Deleting old CovenantedParcel records from this workflow...")
        CovenantedParcel.objects.filter(workflow=workflow).delete()

        print("Creating CovenantedParcel records from this workflow...")
        matched_parcels = Parcel.objects.filter(workflow=workflow, bool_covenant=True)
        flat_covenants = save_flat_covenanted_parcels(matched_parcels)
        return flat_covenants

    def write_match_report(self, workflow, bool_local=False, bool_test=False):
        fieldnames = ['join_string', 'match', 'subject_id',
                      'metadata', 'parcel_metadata', 'num_parcels']

        now = datetime.datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%m')

        # matched_lots = [s for s in self.match_report_zoon if s['match'] is True] # TODO
        # matched_subjects = set([s['subject_id'] for s in matched_lots])

        covenanted_doc_count_zoon = ZooniverseSubject.objects.filter(
            workflow=workflow,
            bool_covenant_final=True
        ).count()

        covenanted_doc_count_manual = ManualCovenant.objects.filter(
            workflow=workflow,
            bool_confirmed=True
        ).count()

        matched_parcel_zoon_count = ZooniverseSubject.objects.filter(
            workflow=workflow,
            bool_covenant_final=True,
            bool_parcel_match=True
        ).count()

        matched_parcel_manual_count = ManualCovenant.objects.filter(
            workflow=workflow,
            bool_confirmed=True,
            bool_parcel_match=True
        ).count()

        matched_lot_count = Parcel.covenant_objects.filter(workflow=workflow).count()

        print(f"{covenanted_doc_count_zoon} covenant subjects")
        print(f"{covenanted_doc_count_manual} manual covenanted docs")
        print(
            f"{matched_lot_count} covenanted lots mapped.")

        filename_tail = f'{workflow.slug}_match_report_{timestamp}.csv'

        if bool_test:
            pass
        elif bool_local:

            outfile_path = os.path.join(
                settings.BASE_DIR, 'data', 'analysis', filename_tail)
            print(f'Writing report to {outfile_path}')
            with(open(outfile_path, 'w') as outfile):
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writerows(self.match_report)
        else:
            print('Creating JoinReport object...')
            csv_buffer = StringIO()
            csv_writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            csv_writer.writeheader()
            csv_writer.writerows(self.match_report)

            csv_file = ContentFile(csv_buffer.getvalue().encode('utf-8'))

            report_obj = JoinReport(
                workflow=workflow,
                # report_csv=csv_file,
                covenanted_doc_count=covenanted_doc_count_zoon+covenanted_doc_count_manual,
                matched_lot_count=matched_lot_count,
                matched_subject_count=matched_parcel_zoon_count+matched_parcel_manual_count,
                created_at=now
            )
            report_obj.report_csv.save(filename_tail, csv_file)
            report_obj.save()

    def match_addition_wide_covenants(self, workflow, parcel_lookup):
        print("Attempting to auto-join previously confirmed addition-wide covenants to parcels ...")

        for covenant in ZooniverseSubject.objects.filter(
            workflow=workflow,
            bool_covenant_final=True,
            match_type_final='AW',
            bool_manual_correction=True
        ).exclude(
            addition_final__in=['', None, 'NONE', 'UNKNOWN']
        ).order_by('addition_final'):
            print(f'{covenant.addition_final}...')
            # Save method should pick up addition-wide covenants
            covenant.save()

        print("Auto-joining addition-wide manual covenants...")
        for covenant in ManualCovenant.objects.filter(
            workflow=workflow,
            bool_confirmed=True,
            cov_type='PT',
        ).exclude(
            addition__in=['', None, 'NONE', 'UNKNOWN']
        ).order_by('addition'):
            print(f'{covenant.addition}...')
            # Save method should pick up addition-wide covenants
            covenant.save()

    def match_parcel_pin_links_zooniverse(self, workflow, workflow_pins_lookup):
        print("Attempting to join Parcel PIN matches on ZooniverseSubjects...")

        # workflow_pins_lookup = {parcel['pin_primary']: parcel['pk'] for parcel in Parcel.objects.filter(workflow=workflow).values('pk', 'pin_primary')}
        # print(workflow_pins_lookup)

        mppls = ManualParcelPINLink.objects.filter(workflow=workflow)

        # matched_zooniverse_subject_ids = []
        matched_parcel_ids = []
        for m in mppls:
            try:
                parcel_id = workflow_pins_lookup[m.parcel_pin]
            except:
                parcel_id = None

            if parcel_id:
                m.zooniverse_subject.parcel_matches.add(parcel_id)
                # matched_zooniverse_subject_ids.append(m.zooniverse_subject.pk)
                matched_parcel_ids.append(workflow_pins_lookup[m.parcel_pin])

        # Update geo union fields, addresses, and bool_parcel_match for final export
        update_objs = []
        for m in mppls:
            m.zooniverse_subject.parcel_matches.add(parcel_id)
            m.zooniverse_subject.bool_parcel_match = True
            m.zooniverse_subject.set_geom_union()
            set_addresses(m.zooniverse_subject)
            update_objs.append(m.zooniverse_subject)
        ZooniverseSubject.objects.bulk_update(
            update_objs, ['geom_union_4326', 'parcel_addresses', 'parcel_city', 'bool_parcel_match'], batch_size=1000)
    
    def match_parcel_pin_links_manual(self, workflow, workflow_pins_lookup):
        print("Attempting to join Parcel PIN matches on ManualCovenants...")
        # TODO: Do same for ManualCovenant

        # workflow_pins_lookup = {parcel['pin_primary']: parcel['pk'] for parcel in Parcel.objects.filter(workflow=workflow).values('pk', 'pin_primary')}

        mppls = ManualCovenantParcelPINLink.objects.filter(workflow=workflow)

        # matched_zooniverse_subject_ids = []
        matched_parcel_ids = []
        for m in mppls:
            try:
                parcel_id = workflow_pins_lookup[m.parcel_pin]
            except:
                parcel_id = None

            if parcel_id:
                m.manual_covenant.parcel_matches.add(parcel_id)
                matched_parcel_ids.append(workflow_pins_lookup[m.parcel_pin])

        # Update geo union fields, addresses, and bool_parcel_match for final export
        update_objs = []
        for m in mppls:
            m.manual_covenant.parcel_matches.add(parcel_id)
            m.manual_covenant.bool_parcel_match = True
            set_addresses(m.manual_covenant)
            update_objs.append(m.manual_covenant)
        ManualCovenant.objects.bulk_update(
            update_objs, ['parcel_addresses', 'parcel_city', 'bool_parcel_match'], batch_size=1000)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            # Get all possible parcel lots to join
            parcel_lookup = build_parcel_spatial_lookups(workflow)

            self.match_parcels_bulk_zoon(workflow, parcel_lookup)
            self.match_parcels_bulk_manual(workflow, parcel_lookup)

            # Join addition-wide covenants
            self.match_addition_wide_covenants(workflow, parcel_lookup)

            # Join covenants by PIN
            workflow_pins_lookup = {parcel['pin_primary']: parcel['pk'] for parcel in Parcel.objects.filter(workflow=workflow).values('pk', 'pin_primary')}
            self.match_parcel_pin_links_zooniverse(workflow, workflow_pins_lookup)
            self.match_parcel_pin_links_manual(workflow, workflow_pins_lookup)

            self.tag_matched_parcels(workflow)

            self.save_flattened_covenants(workflow)

            bool_local = kwargs['local']
            bool_test = kwargs['test']
            self.write_match_report(workflow, bool_local, bool_test)
