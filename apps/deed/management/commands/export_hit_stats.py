import os
import datetime

import pandas as pd

from django.core.management.base import BaseCommand
from django.db.models import Count, OuterRef, Subquery
from django.contrib.postgres.aggregates import StringAgg
from django.core import management
from django.conf import settings

from racial_covenants_processor.storage_backends import PrivateMediaStorage
from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.zoon.utils.zooniverse_load import get_full_url
from apps.deed.models import DeedPage, MatchTerm


class Command(BaseCommand):
    '''Export a real CSV for Zooniverse upload. See also "upload_to_zooniverse.py" to skip this step and import to zooniverse from the app.'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str, help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def save_manifest_local(self, df, version_slug):

        out_csv = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{version_slug}.csv")
        df.to_csv(out_csv, index=False)

        return out_csv

    def build_raw_count_df(self, workflow):
        counts = []
        for m in MatchTerm.objects.filter(deedpage__workflow=workflow).distinct():
            term_count = DeedPage.objects.filter(workflow=workflow, bool_match=True, matched_terms__term=m.term).distinct().count()
            counts.append({'term': m.term, 'term_count': term_count})

        return pd.DataFrame.from_dict(counts).sort_values('term_count', ascending=False)

    def terms_count(self, workflow):
        return DeedPage.objects.filter(
            workflow=workflow,
            pk=OuterRef('pk')
        ).annotate(
            num_terms=Count('matched_terms')
        ).values(
            'num_terms'
        )

    def build_terms_df(self, workflow):

        terms = DeedPage.objects.filter(
            workflow=workflow,
            bool_match=True
        ).annotate(
            term_count=Subquery(self.terms_count(workflow))
        ).values('pk', 'matched_terms__term', 'term_count')

        terms_df = pd.DataFrame.from_dict(terms)
        terms_df.rename(columns={'matched_terms__term': 'term'}, inplace=True)

        return terms_df

    def generate_sample(self, df, term, n=20, bool_combo=False):
        if bool_combo:
            full_term_set = df[(df['term'] == term) & (df['term_count'] > 1)]
        else:
            full_term_set = df[(df['term'] == term) & (df['term_count'] == 1)]

        sample_pks = full_term_set.sample(n=n).pk.to_list()
        print(len(sample_pks))

        sample_df = pd.DataFrame.from_dict(
            DeedPage.objects.filter(
                pk__in=sample_pks
            ).annotate(
                matched_terms_list=StringAgg('matched_terms__term', delimiter=', ')
            ).values('pk', 'workflow__workflow_name', 'matched_terms_list', 'page_image_web')
        )

        sample_df.rename(columns={'workflow__workflow_name': 'workflow'}, inplace=True)

        sample_df = full_term_set.merge(sample_df, how="right", on="pk")

        # print(sample_df)
        return sample_df

    def build_samples_df(self, workflow, raw_counts_df, terms_df):
        samples = []
        for t in raw_counts_df.head(6)['term']:
            samples.append(self.generate_sample(terms_df, t, 20, True))
            samples.append(self.generate_sample(terms_df, t, 20, False))

        samples_df = pd.concat(samples)

        url_prefix = PrivateMediaStorage().url(
            samples_df['page_image_web'].iloc[0]
        ).split('?')[0].replace(samples_df['page_image_web'].iloc[0], '')

        samples_df['page_image_web'] = samples_df['page_image_web'].apply(lambda x: get_full_url(url_prefix, x))

        samples_df = samples_df[[
            'workflow',
            'term',
            'pk',
            'term_count',
            'matched_terms_list',
            'page_image_web',
        ]]

        print(samples_df)
        return samples_df

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            now = datetime.datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%M')

            raw_counts_df = self.build_raw_count_df(workflow)
            version_slug = f"{workflow.slug}_terms_raw_counts_{timestamp}"
            self.save_manifest_local(raw_counts_df, version_slug)

            terms_df = self.build_terms_df(workflow)
            version_slug = f"{workflow.slug}_terms_instance_counts_{timestamp}"
            self.save_manifest_local(terms_df, version_slug)

            samples_df = self.build_samples_df(workflow, raw_counts_df, terms_df)
            version_slug = f"{workflow.slug}_terms_sample_{timestamp}"
            self.save_manifest_local(samples_df, version_slug)
