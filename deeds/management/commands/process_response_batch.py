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

    def handle(self, *args, **kwargs):
        # PART I: Normalize Zooniverse export (handled in load_zooniverse_responses)
        management.call_command('load_zooniverse_responses')

        # TODO: PART II: User_Rank
        management.call_command('calculate_user_rank')
        # self.calculate_user_rank('Ramsey County')

        # TODO PART III: Calculate Mode

        # TODO PART IV: Append and strip 'No' values
