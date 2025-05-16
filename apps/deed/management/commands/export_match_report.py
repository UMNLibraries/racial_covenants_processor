import os
import datetime
import pandas as pd

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.conf import settings

from apps.deed.models import DeedPage
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def save_report_local(self, df, version_slug):
        out_csv = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{version_slug}.csv")
        df.to_csv(out_csv, index=False)

        return out_csv

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:

            workflow = get_workflow_obj(workflow_name)

            image_terms = DeedPage.objects.filter(
                workflow=workflow,
                bool_match=True
            ).select_related(
                'matched_terms__term',
            ).values(
                'pk',
                'matched_terms__term'
            )

            images = DeedPage.objects.filter(
                workflow=workflow,
                bool_match=True
            ).values(
                'pk',
                'doc_num',
                'doc_type',
                'book_id',
                'page_num',
                'batch_id',
                'doc_date',
                's3_lookup',
                'page_image_web_highlighted'
            )

            print(images.count())

            image_terms_df = pd.DataFrame.from_dict(image_terms)
            image_terms_df.rename(columns={'matched_terms__term': 'terms'}, inplace=True)
            image_terms_df = image_terms_df.groupby([
                'pk'
            ]).agg({'terms': lambda x: ', '.join(x)}).reset_index()

            images_df = pd.DataFrame.from_dict(images)
            images_df = images_df.merge(
                image_terms_df,
                how="left",
                on="pk"
            )

            images_df['page_image_web_highlighted'] = settings.AWS_S3_CUSTOM_DOMAIN + '/' + images_df['page_image_web_highlighted']

            print(images_df.shape[0])

            now = datetime.datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%M')
            version_slug = f"{workflow.slug}_hits_{timestamp}"

            match_report_local = self.save_report_local(images_df, version_slug)
