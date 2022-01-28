import os
import datetime
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sklearn.metrics import cohen_kappa_score

from deeds.models import Workflow, ZooniverseResponseFlat, ZooniverseUser, ZooniverseUserRating
from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings

class Command(BaseCommand):
    '''Processes normalized Zooniverse responses to extract real-estate fields and calculate reliability scores. Process brought into the Django world, but based on work by Kevin Ehrman and StarEightyTwo'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str, help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            # PART I: Normalize Zooniverse export
            # management.call_command('load_zooniverse_responses_legacy', workflow=workflow_name)
            #
            # # PART II: User_Rank
            # management.call_command('calculate_user_rank', workflow=workflow_name)

            # TODO PART III: Calculate Mode
            management.call_command('find_consensus_answers', workflow=workflow_name)

            # TODO PART IV: Append and strip 'No' values
