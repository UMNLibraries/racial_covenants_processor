import os
import datetime
import pandas as pd

from django.core.management.base import BaseCommand
from django.db.models import OuterRef
from django.core import management
from django.conf import settings

from apps.zoon.utils.zooniverse_config import get_workflow_obj
from racial_covenants_processor.storage_backends import PrivateMediaStorage
from apps.zoon.models import ZooniverseWorkflow
from apps.deed.models import DeedPage

class Command(BaseCommand):
    '''Prepare OCR hits for Zooniverse upload.'''
    media_storage = PrivateMediaStorage()

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str, help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def url_or_blank(self, page_list, page_num):
        try:
            return [p['page_image_web'] for p in page_list if page_num == int(p['page_num'])][0]
        except:
            return ''

    def get_full_url(self, file_name):
        if file_name == '':
            return ''
        try:
            return self.media_storage.url(file_name).split('?')[0]
        except:
            return ''

    def save_manifest_local(self, df, version_slug):

        out_csv = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{version_slug}.csv")
        df.to_csv(out_csv, index=False)

        return out_csv

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            # manifest = []
            workflow = get_workflow_obj(workflow_name)
            # Get all doc nums with at least one hit
            pages_with_hits = DeedPage.objects.filter(
                workflow=workflow,
                bool_match=True
            ).values('pk', 'doc_num', 'page_num', 'page_image_web', 's3_lookup')

            # Get all pages from all of those docs
            hits_all_pages = DeedPage.objects.filter(
                workflow=workflow,
                doc_num__in=[p['doc_num'] for p in pages_with_hits]
            ).order_by('doc_num', 'page_num').values('doc_num', 'page_num', 'page_image_web')

            # Build manifest based on match with other pages
            print(pages_with_hits.count(), hits_all_pages.count())
            for p in pages_with_hits:
                p['all_pages'] = [ap for ap in hits_all_pages if ap['doc_num'] == p['doc_num']]
                p['page_count'] = len(p['all_pages'])
                if int(p['page_num']) == 1:
                    p['default_frame'] = 1
                    p['#image1'] = self.url_or_blank(p['all_pages'], 1)
                    p['#image2'] = self.url_or_blank(p['all_pages'], 2)
                    p['#image3'] = self.url_or_blank(p['all_pages'], 3)
                else:
                    # Put match page at frame 2 and get page before and after to surround it
                    p['default_frame'] = 2
                    p['#image1'] = self.url_or_blank(p['all_pages'], int(p['page_num']) - 1)
                    p['#image2'] = p['page_image_web']
                    p['#image3'] = self.url_or_blank(p['all_pages'], int(p['page_num']) + 1)


            manifest_df = pd.DataFrame(pages_with_hits)
            manifest_df['#image1'] = manifest_df['#image1'].apply(lambda x: self.get_full_url(x))
            manifest_df['#image2'] = manifest_df['#image2'].apply(lambda x: self.get_full_url(x))
            manifest_df['#image3'] = manifest_df['#image3'].apply(lambda x: self.get_full_url(x))

            manifest_df.rename(columns={
                's3_lookup': '#s3_lookup'
            }, inplace=True)
            print(manifest_df)

            now = datetime.datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%M')
            version_slug = f"{workflow.slug}_zooniverse_manifest_{timestamp}"
            self.save_manifest_local(manifest_df.drop(columns=['all_pages', 'page_image_web']), version_slug)
