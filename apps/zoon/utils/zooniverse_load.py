import os
import pandas as pd

from racial_covenants_processor.storage_backends import PrivateMediaStorage
from apps.deed.models import DeedPage


def url_or_blank(page_list, page_num):
    try:
        # return [p['page_image_web'] for p in page_list if page_num == int(p['page_num'])][0]
        return next(filter(lambda p: page_num == int(p['page_num']), page_list), None)['page_image_web']
    except:
        return ''


def get_full_url(url_prefix, file_name):
    if file_name == '':
        return ''
    try:
        return os.path.join(url_prefix, file_name)
        # return PrivateMediaStorage().url(file_name).split('?')[0]
    except:
        return ''

def build_zooniverse_manifest(workflow):

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
            p['#image1'] = url_or_blank(p['all_pages'], 1)
            p['#image2'] = url_or_blank(p['all_pages'], 2)
            p['#image3'] = url_or_blank(p['all_pages'], 3)
        else:
            # Put match page at frame 2 and get page before and after to surround it
            p['default_frame'] = 2
            p['#image1'] = url_or_blank(p['all_pages'], int(p['page_num']) - 1)
            p['#image2'] = p['page_image_web']
            p['#image3'] = url_or_blank(p['all_pages'], int(p['page_num']) + 1)

    url_prefix = PrivateMediaStorage().url(
        pages_with_hits[0]['page_image_web']
    ).split('?')[0].replace(pages_with_hits[0]['page_image_web'], '')
    print(url_prefix)

    manifest_df = pd.DataFrame(pages_with_hits)
    manifest_df['#image1'] = manifest_df['#image1'].apply(lambda x: get_full_url(url_prefix, x))
    manifest_df['#image2'] = manifest_df['#image2'].apply(lambda x: get_full_url(url_prefix, x))
    manifest_df['#image3'] = manifest_df['#image3'].apply(lambda x: get_full_url(url_prefix, x))

    manifest_df.rename(columns={
        's3_lookup': '#s3_lookup'
    }, inplace=True)
    print(manifest_df)
    return manifest_df.drop(columns=['all_pages', 'page_image_web'])
