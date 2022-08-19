import os
import datetime

from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings

from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.zoon.utils.zooniverse_load import build_zooniverse_manifest


class Command(BaseCommand):
    '''Export a real CSV for Zooniverse upload. See also "upload_to_zooniverse.py" to skip this step and import to zooniverse from the app.'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str, help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

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
            workflow = get_workflow_obj(workflow_name)

            manifest_df = build_zooniverse_manifest(workflow)

            now = datetime.datetime.now()
            timestamp = now.strftime('%Y%m%d_%H%M')
            version_slug = f"{workflow.slug}_zooniverse_manifest_{timestamp}"
            self.save_manifest_local(manifest_df, version_slug)
