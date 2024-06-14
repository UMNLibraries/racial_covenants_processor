import datetime
from django.core import management
from django.core.management.base import BaseCommand

from apps.zoon.models import ManualCovenant

from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''Load a downloaded CSV of ManualCovenant objects into the database and join to ZooniverseSubjects.'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

        parser.add_argument('-f', '--infile', type=str,
                            help='Path to CSV file of manual covenants')

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        infile = kwargs['infile']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
            return False

        if not infile:
            print('Missing infile path. Please specify with --infile.')
            return False
        else:

            workflow = get_workflow_obj(workflow_name)

            print("Loading manual covenants from CSV...")

            # Make custom mapping from model fields to drop IP column
            mapping = {col: col for col in [
                'covenant_text',
                'addition',
                'lot',
                'block',
                'seller',
                'buyer',
                'deed_date',
                'doc_num',
                'city',
                'comments'
            ]}

            static_mapping = {
                'workflow_id': workflow.id,
                'cov_type': 'PS',
                'bool_confirmed': True,
                'bool_parcel_match': False,
                'date_added': datetime.datetime.now(),
                'date_updated': datetime.datetime.now(),
            }

            insert_count = ManualCovenant.objects.from_csv(
                infile, mapping=mapping, static_mapping=static_mapping)
            print("{} records inserted".format(insert_count))

# class ManualCovenant(models.Model):
#     workflow = models.ForeignKey(
#         ZooniverseWorkflow, on_delete=models.CASCADE, null=True)
#     bool_confirmed = models.BooleanField(default=False)
#     covenant_text = models.TextField(blank=True)
#     addition = models.CharField(max_length=500, blank=True)
#     lot = models.TextField(blank=True)
#     block = models.CharField(max_length=500, blank=True)
#     seller = models.CharField(max_length=500, blank=True)
#     buyer = models.CharField(max_length=500, blank=True)
#     deed_date = models.DateField(null=True, blank=True)
#     doc_num = models.CharField(blank=True, max_length=100, db_index=True)

#     city = models.CharField(max_length=500, null=True, blank=True, verbose_name="City")

#     cov_type = models.CharField(choices=MANUAL_COV_OPTIONS, max_length=4, null=True, blank=True)
#     comments = models.TextField(null=True, blank=True)

#     join_candidates = models.JSONField(null=True, blank=True)
#     parcel_matches = models.ManyToManyField('parcel.Parcel')
#     bool_parcel_match = models.BooleanField(default=False, verbose_name="Parcel match?")

#     date_added = models.DateTimeField(auto_now_add=True)
#     date_updated = models.DateTimeField(auto_now=True)