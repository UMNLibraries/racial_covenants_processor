from django.core.management.base import BaseCommand
from django.conf import settings

from apps.zoon.models import ZooniverseSubject, ManualParcelPINLink
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Connect newly loaded or reloaded Zooniverse data to existing
    ManualParcelPINLink objects'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def reconnect_manual_pin_links(self, workflow):
        mpl_objs = ManualParcelPINLink.objects.filter(
            zoon_workflow_id=workflow.zoon_id
        ).only('pk', 'zoon_subject_id')

        mpl_subject_ids = mpl_objs.values_list('zoon_subject_id', flat=True)

        mpl_subjects_lookup = {sbj['zoon_subject_id']: sbj['pk'] for sbj in ZooniverseSubject.objects.filter(
            workflow=workflow,
            zoon_subject_id__in=mpl_subject_ids
        ).values('pk', 'zoon_subject_id')}

        print(
            f'Attaching {mpl_objs.count()} ManualParcelPINLink objects to newly loaded subjects...')
        update_cxes = []
        for cx in mpl_objs:
            cx.workflow_id = workflow.id
            cx.zooniverse_subject_id = mpl_subjects_lookup[cx.zoon_subject_id]
            update_cxes.append(cx)
        ManualParcelPINLink.objects.bulk_update(
            update_cxes, ['workflow_id', 'zooniverse_subject_id'], batch_size=10000)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            self.reconnect_manual_pin_links(workflow)
