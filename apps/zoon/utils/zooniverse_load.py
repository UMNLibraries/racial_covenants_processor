import os
import pandas as pd

from django.db.models import Count, Sum, OuterRef, Subquery, F, Case, When, Value
from django.contrib.postgres.aggregates import StringAgg

from racial_covenants_processor.storage_backends import PrivateMediaStorage
from apps.deed.models import DeedPage


def get_full_url(url_prefix, file_name):
    if file_name == '':
        return ''
    try:
        return os.path.join(url_prefix, file_name)
        # return PrivateMediaStorage().url(file_name).split('?')[0]
    except:
        return ''

def build_zooniverse_manifest(workflow, exclude_ids=[], num_rows=None):
    # Subquery for counting all pages
    doc_page_count = DeedPage.objects.filter(
        workflow=workflow,
        doc_num=OuterRef('doc_num')
    ).values(
        'doc_num'
    ).annotate(
        c=Count('*')
    ).values(
        'c'
    )

    # Get all doc nums with at least one hit
    pages_with_hits = DeedPage.objects.filter(
        workflow=workflow,
        bool_match=True
    ).exclude(
        s3_lookup__in=exclude_ids
    ).annotate(
        matched_terms_list=StringAgg('matched_terms__term', delimiter=', ')
    ).annotate(
        page_count=Subquery(doc_page_count)
    ).annotate(
        default_frame=Case(
            When(
                page_num=1, then=Value(1)
            ),
            default=Value(2)
        ),
        image1=Case(
            When(
                page_num=1, then=F('page_image_web')
            ),
            default=Subquery(
                DeedPage.objects.filter(workflow=workflow, doc_num=OuterRef('doc_num'), page_num=OuterRef('page_num') - 1).order_by('-pk').values('page_image_web')[:1]
            )
        ),
        image2=Case(
            When(
                page_num=1, then=Subquery(
                    DeedPage.objects.filter(workflow=workflow, doc_num=OuterRef('doc_num'), page_num=2).order_by('-pk').values('page_image_web')[:1]
                )
            ),
            default=F('page_image_web')
        ),
        image3=Case(
            When(
                page_num=1, then=Subquery(
                    DeedPage.objects.filter(workflow=workflow, doc_num=OuterRef('doc_num'), page_num=3).order_by('-pk').values('page_image_web')[:1]
                )
            ),
            default=Subquery(
                DeedPage.objects.filter(workflow=workflow, doc_num=OuterRef('doc_num'), page_num=OuterRef('page_num') + 1).order_by('-pk').values('page_image_web')[:1]
            )
        ),
    ).values('pk', 'doc_num', 'page_num', 'page_count', 'default_frame', 'page_image_web', 'image1', 'image2', 'image3', 's3_lookup', 'matched_terms_list')[0:num_rows]

    url_prefix = PrivateMediaStorage().url(
        pages_with_hits[0]['page_image_web']
    ).split('?')[0].replace(pages_with_hits[0]['page_image_web'], '')

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
        'matched_terms_list': 'matched_terms'
    }, inplace=True)
    # print(manifest_df)
    return manifest_df.drop(columns=['page_image_web'])
