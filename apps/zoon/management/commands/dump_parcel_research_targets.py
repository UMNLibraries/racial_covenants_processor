import os
import re
import datetime
import pandas as pd

from django.core.management.base import BaseCommand
from django.core.files.base import File
from django.db.models import Q, F
from django.conf import settings

from apps.zoon.models import ZooniverseSubject, ManualCorrection
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''geojson exporter to either s3 or local file'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def save_csv_local(self, df, workflow):
        out_csv = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{workflow.slug}-parcel-research-targets-{datetime.datetime.now().strftime('%Y%m%d')}.csv")
        df.to_csv(out_csv, index=False)

        return out_csv


    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

        research_subjects = ZooniverseSubject.objects.filter(
            Q(manualcorrection__comments__icontains="not sure") | Q(manualcorrection__comments__icontains="no idea"),
            workflow=workflow,
            bool_parcel_match=False
        ).annotate(
            comments=F('manualcorrection__comments')
        )

        df = pd.DataFrame(research_subjects.values(
            'id',
            'zoon_subject_id',
            'comments'
        ))

        extracted_df = df['comments'].str.extractall(
            r'Parcel (?:No. |object |#|object no. )\(?(\d+)',
            flags=re.IGNORECASE
        )
        df['parcel_pks'] = extracted_df.groupby(level=0)[0].apply(lambda x: ', '.join(x))

        print(df)

        print(research_subjects.count())
        self.save_csv_local(df, workflow)