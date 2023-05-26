import os
import datetime
import tempfile
import pandas as pd

from django.core.management.base import BaseCommand
from django.core.files.base import File
from django.conf import settings

from apps.parcel.models import CSVExport
from apps.parcel.utils.export_utils import build_unmapped_df
from apps.zoon.models import MATCH_TYPE_OPTIONS
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''CSV exporter to either s3 or local file'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        parser.add_argument('-l', '--local', action='store_true',
                            help='Save to local csv in "main_exports" dir, rather than Django object/S3')

    def save_csv_local(self, df, version_slug):
        out_csv = os.path.join(
            settings.BASE_DIR, 'data', 'main_exports', f"{version_slug}.csv")
        df.to_csv(out_csv, index=False)

        return out_csv

    def save_csv_model(self, df, version_slug, workflow, created_at):
        # Convert to shapefile and serve it to the user
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_file_path = os.path.join(tmp_dir, f'{version_slug}.csv')
            df.to_csv(tmp_file_path, index=False)

            csv_export_obj = CSVExport(
                workflow=workflow,
                covenant_count=df.shape[0],
                created_at = created_at
            )

            # Using File
            with open(tmp_file_path, 'rb') as f:
                csv_export_obj.csv.save(f'{version_slug}.csv', File(f))
            csv_export_obj.save()
            return csv_export_obj

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)

            covenants_df = build_unmapped_df(workflow)

            print(covenants_df)

            now = datetime.datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%M')
            version_slug = f"{workflow.slug}_covenants_unmapped_{timestamp}"

            if kwargs['local']:
                csv_local = self.save_csv_local(covenants_df, version_slug)
            else:
                # Save to zipped shp in Django storages/model
                csv_export_obj = self.save_csv_model(covenants_df, version_slug, workflow, now)
