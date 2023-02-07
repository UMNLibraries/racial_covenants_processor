import os
import urllib
import random
import numpy as np
import pandas as pd

from django.db.models import F, Case, When, Value
from django.contrib.postgres.aggregates import StringAgg

from racial_covenants_processor.storage_backends import PrivateMediaStorage
from apps.deed.models import DeedPage


def get_image_url_prefix(img_rel_path):
    url_prefix = PrivateMediaStorage().url(
        img_rel_path
    ).split('?')[0].replace(urllib.parse.quote(img_rel_path), '')
    return url_prefix

def get_full_url(url_prefix, file_name):
    if file_name == '':
        return ''
    try:
        return os.path.join(url_prefix, urllib.parse.quote(file_name))
        # return PrivateMediaStorage().url(file_name).split('?')[0]
    except:
        return ''

def int_str_or_blank(value):
    try:
        return str(int(value))
    except:
        return ''

def build_zooniverse_manifest(workflow, exclude_ids=[], num_rows=None):

    # Get random IDs
    matching_ids = DeedPage.objects.filter(
        workflow=workflow,
        bool_match=True
    ).exclude(
        s3_lookup__in=exclude_ids
    ).values_list('id', flat=True)

    if num_rows:
        final_set = random.sample(list(matching_ids), num_rows)
    else:
        final_set = matching_ids

    # Get all doc nums with at least one hit
    pages_with_hits = DeedPage.objects.filter(
        id__in=final_set
    ).annotate(
        matched_terms_list=StringAgg('matched_terms__term', delimiter=', ')
    ).annotate(
        default_frame=Case(
            When(
                prev_page_image_web__in=[None, ''], then=Value(1)
            ),
            default=Value(2)
        ),
        image1=Case(
            When(
                prev_page_image_web__in=[None, ''], then=F('page_image_web')
            ),
            default=F('prev_page_image_web')
        ),
        image2=Case(
            When(
                prev_page_image_web__in=[None, ''], then=F('next_page_image_web')
            ),
            default=F('page_image_web')
        ),
        image3=Case(
            When(
                next_page_image_web__in=[None, ''], then=Value(None)
            ),
            When(
                default_frame=1, then=F('next_next_page_image_web')
            ),
            default=F('next_page_image_web')
        )
    ).values('pk', 'doc_num', 'page_num', 'split_page_num', 'doc_page_count', 'default_frame', 'page_image_web', 'image1', 'image2', 'image3', 's3_lookup', 'matched_terms_list')[0:num_rows]

    url_prefix = get_image_url_prefix(pages_with_hits[0]['page_image_web'])
    # url_prefix = PrivateMediaStorage().url(
    #     pages_with_hits[0]['page_image_web']
    # ).split('?')[0].replace(pages_with_hits[0]['page_image_web'], '')

    manifest_df = pd.DataFrame(pages_with_hits)
    manifest_df.rename(columns={
        'image1': '#image1',
        'image2': '#image2',
        'image3': '#image3',
    }, inplace=True)
    manifest_df['#image1'] = manifest_df['#image1'].apply(lambda x: get_full_url(url_prefix, x))
    manifest_df['#image2'] = manifest_df['#image2'].apply(lambda x: get_full_url(url_prefix, x))
    manifest_df['#image3'] = manifest_df['#image3'].apply(lambda x: get_full_url(url_prefix, x))

    manifest_df['page_num_str'] = manifest_df['page_num'].apply(lambda x: int_str_or_blank(x))
    manifest_df.drop(columns=['page_num'], inplace=True)
    manifest_df.rename(columns={'page_num_str': 'page_num'}, inplace=True)

    manifest_df['split_page_num_str'] = manifest_df['split_page_num'].apply(lambda x: int_str_or_blank(x))
    manifest_df.drop(columns=['split_page_num'], inplace=True)
    manifest_df.rename(columns={'split_page_num_str': 'split_page_num'}, inplace=True)

    manifest_df.rename(columns={
        's3_lookup': '#s3_lookup',
        'matched_terms_list': 'matched_terms',
        'doc_page_count': 'page_count'
    }, inplace=True)
    # print(manifest_df)
    return manifest_df.drop(columns=['page_image_web'])
