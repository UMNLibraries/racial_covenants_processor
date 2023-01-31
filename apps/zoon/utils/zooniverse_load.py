import os
import urllib
import random
import pandas as pd

from django.db.models import Count, Sum, OuterRef, Subquery, F, Q, Case, When, Exists, Value
# from django.contrib.postgres.aggregates import StringAgg

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

    # Subquery for counting all pages
    # doc_page_count = DeedPage.objects.filter(
    #     workflow=workflow,
    #     doc_num=OuterRef('doc_num')
    # ).values(
    #     'doc_num'
    # ).annotate(
    #     c=Count('*')
    # ).values(
    #     'c'
    # )

    # Get all doc nums with at least one hit
    pages_with_hits = DeedPage.hit_objects.filter(
        id__in=final_set
    # pages_with_hits = DeedPage.objects.filter(
    #     workflow=workflow,
    #     bool_match=True
    # ).exclude(
    #     s3_lookup__in=exclude_ids
    # ).annotate(
    #     matched_terms_list=StringAgg('matched_terms__term', delimiter=', ')
    # ).annotate(
    #     page_count=Subquery(doc_page_count)
    ).annotate(
        default_frame=Case(
            When(
                prev_page_image_web=None, then=Value(1)
            ),
            default=Value(2)
        ),
        image1=Case(
            When(
                prev_page_image_web=None, then=F('page_image_web')
            ),
            default=F('prev_page_image_web')
        ),
        image2=Case(
            When(
                prev_page_image_web=None, then=F('next_page_image_web')
            ),
            default=F('page_image_web')
        ),
        image3=Case(
            When(
                next_page_image_web=None, then=Value(None)
            ),
            When(
                default_frame=1, then=F('next_next_page_image_web')
            ),
            default=F('next_page_image_web')
        )
    # ).annotate(
        # default_frame=Case(
        #     When(
        #         Q(page_num=1) & Q(split_page_num=None), then=Value(1)
        #     ),
        #     When(
        #         split_page_num=1, then=Value(1)
        #     ),
        #     When(
        #         split_page_num__gt=1, then=Value(2)
        #     ),
        #     default=Value(2)
        # ),
        # TODO: Change logic to use prev/next image from model manager
        # image1=Case(
        #     When(
        #         Q(page_num=1) & Q(split_page_num=None), then=F('page_image_web')
        #     ),
        #     When(
        #         split_page_num=1, then=F('page_image_web')
        #     ),
        #     When(
        #         split_page_num__gt=1, then=Subquery(
        #             DeedPage.objects.filter(workflow=workflow, doc_num=OuterRef('doc_num'), split_page_num=OuterRef('split_page_num') - 1).order_by('-pk').values('page_image_web')[:1]
        #         )
        #     ),
        #     default=Subquery(
        #         DeedPage.objects.filter(workflow=workflow, doc_num=OuterRef('doc_num'), page_num=OuterRef('page_num') - 1).order_by('-pk').values('page_image_web')[:1]
        #     )
        # ),
        # image2=Case(
        #     When(
        #         page_num=1, then=Subquery(
        #             DeedPage.objects.filter(workflow=workflow, doc_num=OuterRef('doc_num'), page_num=2).order_by('-pk').values('page_image_web')[:1]
        #         )
        #     ),
        #     When(
        #         split_page_num=1, then=Subquery(
        #             DeedPage.objects.filter(workflow=workflow, doc_num=OuterRef('doc_num'), split_page_num=2).order_by('-pk').values('page_image_web')[:1]
        #         )
        #     ),
        #     default=F('page_image_web')
        # ),
        # image3=Case(
        #     When(
        #         page_num=1, then=Subquery(
        #             DeedPage.objects.filter(workflow=workflow, doc_num=OuterRef('doc_num'), page_num=3).order_by('-pk').values('page_image_web')[:1]
        #         )
        #     ),
        #     When(
        #         split_page_num=1, then=Subquery(
        #             DeedPage.objects.filter(workflow=workflow, doc_num=OuterRef('doc_num'), split_page_num=3).order_by('-pk').values('page_image_web')[:1]
        #         )
        #     ),
        #     When(
        #         split_page_num__gt=1, then=Subquery(
        #             DeedPage.objects.filter(workflow=workflow, doc_num=OuterRef('doc_num'), split_page_num=OuterRef('split_page_num') + 1).order_by('-pk').values('page_image_web')[:1]
        #         )
        #     ),
        #     default=Subquery(
        #         DeedPage.objects.filter(workflow=workflow, doc_num=OuterRef('doc_num'), page_num=OuterRef('page_num') + 1).order_by('-pk').values('page_image_web')[:1]
        #     )
        # ),
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

    manifest_df.rename(columns={
        's3_lookup': '#s3_lookup',
        'matched_terms_list': 'matched_terms',
        'doc_page_count': 'page_count'
    }, inplace=True)
    # print(manifest_df)
    return manifest_df.drop(columns=['page_image_web'])
