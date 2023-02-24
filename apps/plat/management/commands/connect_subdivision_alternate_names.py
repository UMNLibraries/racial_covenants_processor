from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings

from apps.plat.models import Subdivision, SubdivisionAlternateName
from apps.parcel.models import Parcel
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Connect newly loaded or reloaded Subdivision data to existing
    SubdivisionAlternateName objects'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def reconnect_subdivision_alternate_names(self, workflow):
        san_objs = SubdivisionAlternateName.objects.filter(
            zoon_workflow_id=workflow.zoon_id
        ).only('pk', 'subdivision_name')

        san_subdivision_names = san_objs.values_list('subdivision_name', flat=True)

        san_subdivisions_lookup = {subdivision['name']: subdivision['pk'] for subdivision in Subdivision.objects.filter(
            workflow=workflow,
            name__in=san_subdivision_names
        ).values('pk', 'name')}

        print(
            f'Attaching {san_objs.count()} SubdivisionAlternateName objects to newly loaded Subdivisions...')
        update_cxes = []
        for cx in san_objs:
            cx.workflow_id = workflow.id
            cx.subdivision_id = san_subdivisions_lookup[cx.subdivision_name]
            update_cxes.append(cx)
        SubdivisionAlternateName.objects.bulk_update(
            update_cxes, ['workflow_id', 'subdivision_id'], batch_size=10000)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            self.reconnect_subdivision_alternate_names(workflow)
            management.call_command(
                'connect_subdivision_alternate_names_to_parcels', workflow=workflow_name)
