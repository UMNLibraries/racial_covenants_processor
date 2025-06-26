from django.core.management.base import BaseCommand

from apps.zoon.utils.zooniverse_config import get_workflow_obj
from apps.zoon.utils.django_export import dump_cx_model_backups

class Command(BaseCommand):
    '''
    This command exports flat CSV files of Django ZooniverseSubject data, mainly for migration to a new workflow or as an archival tool.

    Note that this only exports finalized ZooniverseSubject data and associated foreign keys, not raw response data or reducer output.
    '''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            workflow = get_workflow_obj(workflow_name)
            outfile = dump_cx_model_backups(workflow, 'zoon', 'ZooniverseSubject')
