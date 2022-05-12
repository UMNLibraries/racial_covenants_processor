from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Subquery, OuterRef, F

from apps.zoon.models import ZooniverseSubject, ManualCorrection
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Connect newly loaded or reloaded Zooniverse data to existing
    ManualCorrection objects, and set initial "final" values.'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def reconnect_manual_corrections(self, workflow):
        cx_objs = ManualCorrection.objects.filter(
            zoon_workflow_id=workflow.zoon_id
        ).only('pk', 'zoon_subject_id')

        cx_subject_ids = cx_objs.values_list('zoon_subject_id', flat=True)

        cx_subjects_lookup = {sbj['zoon_subject_id']: sbj['pk'] for sbj in ZooniverseSubject.objects.filter(
            workflow=workflow,
            zoon_subject_id__in=cx_subject_ids
        ).values('pk', 'zoon_subject_id')}
        print(len(cx_subjects_lookup.keys()))

        print(
            f'Attaching {cx_objs.count()} ManualCorrection objects to newly loaded subjects...')
        update_cxes = []
        for cx in cx_objs:
            cx.workflow_id = workflow.id
            cx.zooniverse_subject_id = cx_subjects_lookup[cx.zoon_subject_id]
            update_cxes.append(cx)
        ManualCorrection.objects.bulk_update(
            update_cxes, ['workflow_id', 'zooniverse_subject_id'], batch_size=10000)

    def set_string_final(self, workflow, attr_root):
        null_kwargs = {f'manualcorrection__{attr_root}__isnull': True}
        blank_kwargs = {f'manualcorrection__{attr_root}__exact': ''}

        # This is crazy town, but updating in bulk across foreign keys isn't for wimps
        update_kwargs_outer = {
            f'{attr_root}_final': Subquery(
                ManualCorrection.objects.filter(
                    zooniverse_subject=OuterRef('pk')
                ).values(attr_root)[:1]
            )
        }

        ZooniverseSubject.objects.filter(
            workflow=workflow
        ).exclude(
            **null_kwargs
        ).exclude(
            **blank_kwargs
        ).update(
            **update_kwargs_outer
        )

    def set_final_values(self, workflow):
        '''Once you are saving subjects one by one, the code in the model definition handles this. But you need to set initial values all at once, rather than looping through each.'''
        print('Setting "final" values, taking into account re-connected ManualCorrections')

        ZooniverseSubject.objects.filter(
            workflow=workflow,
            manualcorrection__isnull=False
        ).update(
            bool_manual_correction=True
        )

        manually_cxed_subjects = ManualCorrection.objects.filter(
            workflow=workflow
        ).values_list('zoon_subject_id', flat=True)

        ZooniverseSubject.objects.filter(
            workflow=workflow,
            zoon_subject_id__in=manually_cxed_subjects
            # manualcorrection__bool_covenant__isnull=False
        ).update(
            bool_covenant_final=Subquery(
                ManualCorrection.objects.filter(
                    zooniverse_subject=OuterRef('pk')
                ).values('bool_covenant')[:1]
            )
        )

        ZooniverseSubject.objects.filter(
            workflow=workflow,
            manualcorrection__deed_date__isnull=False
        ).update(
            deed_date_final=Subquery(
                ManualCorrection.objects.filter(
                    zooniverse_subject=OuterRef('pk')
                ).values('deed_date')[:1]
            )
        )

        self.set_string_final(workflow, 'covenant_text')
        self.set_string_final(workflow, 'addition')
        self.set_string_final(workflow, 'lot')
        self.set_string_final(workflow, 'block')
        self.set_string_final(workflow, 'seller')
        self.set_string_final(workflow, 'buyer')
        self.set_string_final(workflow, 'match_type')

        print('Set everything else w/o manualcorrection to zooniverse consensus...')
        ZooniverseSubject.objects.filter(
            workflow=workflow,
            manualcorrection__isnull=True
        ).update(
            bool_manual_correction=False,
            bool_covenant_final=F('bool_covenant'),
            covenant_text_final=F('covenant_text'),
            addition_final=F('addition'),
            lot_final=F('lot'),
            block_final=F('block'),
            seller_final=F('seller'),
            buyer_final=F('buyer'),
            deed_date_final=F('deed_date'),
            match_type_final=F('match_type'),
        )

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            self.reconnect_manual_corrections(workflow)
            self.set_final_values(workflow)
