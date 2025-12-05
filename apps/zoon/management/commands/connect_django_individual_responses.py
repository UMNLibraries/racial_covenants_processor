from django.core.management.base import BaseCommand
from django.conf import settings

from apps.zoon.models import ZooniverseSubject, ZooniverseResponseProcessed
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Connect newly loaded or reloaded Zooniverse data to existing
    ZooniverseResponseProcessed objects'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def reconnect_objs(self, workflow):
        resp_objs = ZooniverseResponseProcessed.objects.filter(
            workflow=workflow,
            zoon_subject_id__isnull=False
        ).only('pk', 'zoon_subject_id')

        resp_subject_ids = resp_objs.values_list('zoon_subject_id', flat=True)

        resp_subjects_lookup = {sbj['zoon_subject_id']: sbj['pk'] for sbj in ZooniverseSubject.objects.filter(
            workflow=workflow,
            zoon_subject_id__in=resp_subject_ids
        ).values('pk', 'zoon_subject_id')}

        print(f"found {len(resp_subjects_lookup)} matching subjects.")

        print(
            f'Attaching {resp_objs.count()} ZooniverseResponseProcessed objects to newly loaded subjects...')
        update_objs = []
        for obj in resp_objs:
            obj.workflow_id = workflow.id
            obj.subject_id = resp_subjects_lookup[obj.zoon_subject_id]
            update_objs.append(obj)
        ZooniverseResponseProcessed.objects.bulk_update(
            update_objs, ['workflow_id', 'subject_id'], batch_size=10000)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            self.reconnect_objs(workflow)
