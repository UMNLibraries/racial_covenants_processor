from django.core.management.base import BaseCommand
from django.conf import settings

from apps.plat.models import Plat, PlatAlternateName
from apps.parcel.models import Parcel
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Connect newly loaded or reloaded Zooniverse data to existing
    PlatAlternateName objects'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def reconnect_plat_alternate_names(self, workflow):
        pan_objs = PlatAlternateName.objects.filter(
            zoon_workflow_id=workflow.zoon_id
        ).only('pk', 'plat_name')

        pan_plat_names = pan_objs.values_list('plat_name', flat=True)

        pan_plats_lookup = {plat['plat_name']: plat['pk'] for plat in Plat.objects.filter(
            workflow=workflow,
            plat_name__in=pan_plat_names
        ).values('pk', 'plat_name')}

        print(
            f'Attaching {pan_objs.count()} PlatAlternateName objects to newly loaded Plats...')
        update_cxes = []
        for cx in pan_objs:
            cx.workflow_id = workflow.id
            cx.plat_id = pan_plats_lookup[cx.plat_name]
            update_cxes.append(cx)
        PlatAlternateName.objects.bulk_update(
            update_cxes, ['workflow_id', 'plat_id'], batch_size=10000)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            self.reconnect_plat_alternate_names(workflow)
