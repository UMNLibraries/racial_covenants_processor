from django.db.models import F
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.zoon.models import ZooniverseSubject
from apps.deed.models import DeedPage
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Checks if deed images failed to join to subject because a highlighted version exists that somehow was not present in data coming back from Zoonivere'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def get_deedpage_lookup(self, workflow):
        dps = DeedPage.objects.filter(workflow=workflow).values(
            'pk',
            's3_lookup',
            'prev_page_image_lookup',
            'next_page_image_lookup'
        )

        return {
            dp['s3_lookup']: {
                'pk': dp['pk'], 
                'prev_page_image_lookup': dp['prev_page_image_lookup'],
                'next_page_image_lookup': dp['next_page_image_lookup']
            } for dp in dps
        }

    def find_hits_with_missing_images(self, workflow):
        hits = ZooniverseSubject.objects.filter(
            workflow=workflow
        ).annotate(
            p1_lookup=F('subject_1st_page__s3_lookup')
        ).annotate(
            p2_lookup=F('subject_2nd_page__s3_lookup')
        ).annotate(
            p3_lookup=F('subject_3rd_page__s3_lookup')
        )
        return hits
    
    def set_prev_page(self, workflow, hit, dp_obj, position):
        position_ordinals = {
            1: '1st', 2: '2nd', 3: '3rd'
        }
        try:
            prev_page = DeedPage.objects.get(workflow=workflow, s3_lookup=dp_obj['prev_page_image_lookup'])
            setattr(prev_page, f'zooniverse_subject_{position_ordinals[position]}_page_id', hit.id)
            return prev_page
        except DeedPage.DoesNotExist:
            return None
    
    def set_next_page(self, workflow, hit, dp_obj, position):
        position_ordinals = {
            1: '1st', 2: '2nd', 3: '3rd'
        }
        try:
            next_page = DeedPage.objects.get(workflow=workflow, s3_lookup=dp_obj['next_page_image_lookup'])
            setattr(next_page, f'zooniverse_subject_{position_ordinals[position]}_page_id', hit.id)
            return next_page
        except DeedPage.DoesNotExist:
            return None

    
    def fill_missing_images(self, workflow, hits_with_missing_images, dps):
        update_dps = []
        for hit in hits_with_missing_images:
            if not hit.subject_legacy.first():
                print(f'WEIRD ONE WITH NO LINKED DEEDPAGE: {hit.zoon_subject_id}')

            elif hit.subject_legacy.first().s3_lookup in [hit.p1_lookup, hit.p2_lookup, hit.p3_lookup]:
                print(f'already matched: {hit.zoon_subject_id}')
            else:
                print(hit.zoon_subject_id, hit.subject_legacy.first().s3_lookup)

                main_dp = hit.subject_legacy.first()

                missing_frames = []
                if not hit.p1_lookup:
                    missing_frames.append(1)
                if not hit.p2_lookup:
                    missing_frames.append(2)
                if not hit.p3_lookup:
                    missing_frames.append(3)

                print(missing_frames)

                if missing_frames == [1]:
                    # fill in first frame
                    main_dp.zooniverse_subject_1st_page = hit
                    update_dps.append(main_dp)
                elif missing_frames == [2]:
                    # fill in second frame (most common)
                    main_dp.zooniverse_subject_2nd_page = hit
                    update_dps.append(main_dp)
                elif missing_frames == [1, 3]:
                    # ignore 3rd frame I guess
                    main_dp.zooniverse_subject_1st_page = hit
                    update_dps.append(main_dp)
                elif missing_frames == [2, 3]:
                    main_dp.zooniverse_subject_2nd_page = hit
                    next_page = self.set_next_page(workflow, hit, dps[main_dp.s3_lookup], 3)
                    update_dps.extend([main_dp, next_page])
                elif missing_frames == [1, 2]:
                    main_dp.zooniverse_subject_2nd_page = hit
                    prev_page = self.set_prev_page(workflow, hit, dps[main_dp.s3_lookup], 1)
                    update_dps.extend([main_dp, prev_page])
                elif missing_frames == [1, 2, 3]:
                    main_dp.zooniverse_subject_2nd_page = hit
                    prev_page = self.set_prev_page(workflow, hit, dps[main_dp.s3_lookup], 1)
                    next_page = self.set_next_page(workflow, hit, dps[main_dp.s3_lookup], 3)
                    update_dps.extend([main_dp, prev_page, next_page])

        # Bulk update
        DeedPage.objects.bulk_update(
            [dp for dp in update_dps if dp is not None], ['zooniverse_subject_1st_page_id', 'zooniverse_subject_2nd_page_id', 'zooniverse_subject_3rd_page_id'])


    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            hits_with_missing_images = self.find_hits_with_missing_images(workflow)
            print(hits_with_missing_images.count())

            dps = self.get_deedpage_lookup(workflow)

            results = self.fill_missing_images(workflow, hits_with_missing_images, dps)
