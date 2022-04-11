import os

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Subquery, OuterRef, F

from zoon.models import ZooniverseWorkflow, ZooniverseSubject, ExtraParcelCandidate
from zoon.utils.zooniverse_config import get_workflow_version


class Command(BaseCommand):
    '''Connect newly loaded or reloaded Zooniverse data to existing
    ExtraParcelCandidate objects'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def reconnect_extra_parcels(self, workflow):
        epc_objs = ExtraParcelCandidate.objects.filter(
            zoon_workflow_id=workflow.zoon_id
        ).only('pk', 'zoon_subject_id')

        epc_subject_ids = epc_objs.values_list('zoon_subject_id', flat=True)

        epc_subjects_lookup = {sbj['zoon_subject_id']: sbj['pk'] for sbj in ZooniverseSubject.objects.filter(
            workflow=workflow,
            zoon_subject_id__in=epc_subject_ids
        ).values('pk', 'zoon_subject_id')}

        print(
            f'Attaching {epc_objs.count()} ExtraParcelCandidate objects to newly loaded subjects...')
        update_cxes = []
        for cx in epc_objs:
            cx.workflow_id = workflow.id
            cx.zooniverse_subject_id = epc_subjects_lookup[cx.zoon_subject_id]
            update_cxes.append(cx)
        ExtraParcelCandidate.objects.bulk_update(
            update_cxes, ['workflow_id', 'zooniverse_subject_id'], batch_size=10000)

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

            self.reconnect_extra_parcels(workflow)
