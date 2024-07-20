from django.core.management.base import BaseCommand
from django.conf import settings

from apps.parcel.models import Parcel, ManualParcelCandidate
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Connect newly loaded or reloaded Zooniverse data to existing
    ManualParcelCandidate objects'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def reconnect_manual_parcel_candidates(self, workflow):
        mpc_objs = ManualParcelCandidate.objects.filter(
            workflow_name=workflow.workflow_name
        ).only('pk', 'parcel_pin_primary')

        mpc_parcel_ids = mpc_objs.values_list('parcel_pin_primary', flat=True)

        mpc_parcels_lookup = {sbj['pin_primary']: sbj['pk'] for sbj in Parcel.objects.filter(
            workflow=workflow,
            pin_primary__in=mpc_parcel_ids
        ).values('pk', 'pin_primary')}

        print(
            f'Attaching {mpc_objs.count()} ManualParcelCandidate objects to newly loaded parcels...')
        update_cxes = []
        for cx in mpc_objs:
            cx.workflow_id = workflow.id
            cx.parcel_id = mpc_parcels_lookup[cx.parcel_pin_primary]
            update_cxes.append(cx)
        ManualParcelCandidate.objects.bulk_update(
            update_cxes, ['workflow_id', 'parcel_id'], batch_size=10000)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            self.reconnect_manual_parcel_candidates(workflow)
