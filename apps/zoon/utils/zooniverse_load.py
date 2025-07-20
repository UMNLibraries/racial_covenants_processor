import os
import urllib
import random
import numpy as np
import pandas as pd

from panoptes_client import Panoptes, Project, Subject, SubjectSet

from django.db.models import F, Case, When, Value, Q
from django.contrib.postgres.aggregates import StringAgg

from racial_covenants_processor.storage_backends import PrivateMediaStorage
from apps.deed.models import DeedPage

from django.conf import settings


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

    # exclude_kwargs = {
    #     'bool_exception': True  # Usually bool_match and bool_exception are mutually exclusive, but there are some cases where they are not (e.g. migrated workflow with previous Zooniverse work we don't want to repeat)
    # }
    # if len(exclude_ids) > 0:
    #     # Passing an empty list to exclude messes up queryset, so only add this if it's filled out
    #     exclude_kwargs['s3_lookup__in'] = exclude_ids

    if len(exclude_ids) > 0:
        s3_lookups = [ex['#s3_lookup'] for ex in exclude_ids]

        # Get random IDs
        matching_ids = DeedPage.objects.filter(
            workflow=workflow,
            bool_match=True
        ).exclude(
            bool_exception=True # Usually bool_match and bool_exception are mutually exclusive, but there are some cases where they are not (e.g. migrated workflow with previous Zooniverse work we don't want to repeat)
        ).exclude(
            s3_lookup__in=s3_lookups
        ).values_list('id', flat=True)

    else:

        # Get random IDs
        matching_ids = DeedPage.objects.filter(
            workflow=workflow,
            bool_match=True
        ).exclude(
            bool_exception=True # Usually bool_match and bool_exception are mutually exclusive, but there are some cases where they are not (e.g. migrated workflow with previous Zooniverse work we don't want to repeat)
        ).values_list('id', flat=True)

    if num_rows:
        # Take num_rows or length of matching_ids, whichever is lower
        num_rows_final = min([len(matching_ids), num_rows])
        final_set = random.sample(list(matching_ids), num_rows_final)
    else:
        final_set = matching_ids

    if len(final_set) > 0:
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
                    Q(prev_page_image_web__in=[None, '']) & Q(page_image_web_highlighted__in=[None, '']),
                    then=F('page_image_web')
                ),
                When(  # Almost the same as the previous when but for null vs. blank issues
                    Q(prev_page_image_web__in=[None, '']) & Q(page_image_web_highlighted__isnull=True),
                    then=F('page_image_web')
                ),
                When(
                    prev_page_image_web__in=[None, ''],
                    then=F('page_image_web_highlighted')
                ),
                default=F('prev_page_image_web')
            ),
            image2=Case(
                When(
                    prev_page_image_web__in=[None, ''], then=F('next_page_image_web')
                ),
                # Otherwise use main image, which may be either page_image_web or page_image_highlighted
                When(
                    page_image_web_highlighted__in=[None, ''], then=F('page_image_web')
                ),
                When(  # Almost the same as the previous when but for null vs. blank issues
                    page_image_web_highlighted__isnull=True, then=F('page_image_web')
                ),
                # default=F('page_image_web')
                default=F('page_image_web_highlighted')
            ),
            image3=Case(
                When(
                    next_page_image_web__in=[None, ''], then=Value(None)
                ),
                When(
                    default_frame=1, then=F('next_next_page_image_web')
                ),
                default=F('next_page_image_web')
            ),
            # Duplicates logic above (sorry) to fill out image lookups
            imagelookup1=Case(
                When(
                    prev_page_image_lookup__in=[None, ''], then=F('s3_lookup')
                ),
                default=F('prev_page_image_lookup')
            ),
            imagelookup2=Case(
                When(
                    prev_page_image_lookup__in=[None, ''], then=F('next_page_image_lookup')
                ),
                default=F('s3_lookup')
            ),
            imagelookup3=Case(
                When(
                    next_page_image_lookup__in=[None, ''], then=Value(None)
                ),
                When(
                    default_frame=1, then=F('next_next_page_image_lookup')
                ),
                default=F('next_page_image_lookup')
            )
        ).values('pk', 'doc_num', 'page_num', 'split_page_num', 'doc_page_count', 'default_frame', 'page_image_web', 'image1', 'image2', 'image3', 'imagelookup1', 'imagelookup2', 'imagelookup3', 's3_lookup', 'matched_terms_list')[0:num_rows]

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

        image_lookup_cols = ['imagelookup1', 'imagelookup2', 'imagelookup3']
        manifest_df['image_ids'] = manifest_df[image_lookup_cols].fillna(value='').apply(lambda row: ','.join( row.values.astype(str)), axis=1)
        manifest_df['image_ids'] = manifest_df['image_ids'].apply(lambda x: ','.join([val for val in x.split(',') if val != '']))

        manifest_df = manifest_df.drop(columns=image_lookup_cols)

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

    return pd.DataFrame()


def connect_to_zooniverse():
    Panoptes.connect(username=settings.ZOONIVERSE_USERNAME, password=settings.ZOONIVERSE_PASSWORD)
    project = Project.find(slug=settings.ZOONIVERSE_PROJECT_SLUG)

    return project


def get_subject_set(project, workflow):
    try:
        subject_set = SubjectSet.where(project_id=project.id, display_name=workflow.workflow_name).next()
        print(f"Found existing subjet set {workflow.workflow_name} ({subject_set.id}).")

    except StopIteration:
        print(f"No matching subject set found.")
        return False
    return subject_set


def get_or_create_subject_set(project, workflow):
    try:
        subject_set = SubjectSet.where(project_id=project.id, display_name=workflow.workflow_name).next()
        print(f"Found existing subjet set {workflow.workflow_name} ({subject_set.id}).")

    except StopIteration:
        print(f"No matching subject set found. Creating '{workflow.workflow_name}'...")
        subject_set = SubjectSet()
        subject_set.links.project = project
        subject_set.display_name = workflow.workflow_name
        subject_set.save()
        print(f"Subject set {subject_set.id} created.")
    return subject_set


def get_existing_subjects(subject_set):
    print("Getting existing subjects in subject set...")
    subject_set_objs = []
    for subject in subject_set.subjects:
        subject_obj = {'subject_id': subject.id}
        subject_obj.update(subject.metadata)
        subject_set_objs.append(subject_obj)
    return subject_set_objs
    # return [subject.metadata for subject in subject_set.subjects]


def delete_zooniverse_subjects(subject_set, subject_ids=[]):
    subject_set.remove(subject_ids)