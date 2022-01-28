import os
import pandas as pd

from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        df_django = pd.read_csv(os.path.join(settings.BASE_DIR, 'data', 'zooniverse_exports', 'reliability_scores_20220125.csv'))

        df_legacy = pd.read_csv(os.path.join(settings.BASE_DIR, 'data', 'zooniverse_exports', 'legacy', 'reliability_scores_2022_1_25.csv'))

        difference = df_legacy.merge(
            df_django,
            how='left',
            left_on='index',
            right_on="zoon_name"
        )

        print(difference[difference['zoon_name'].isna()])

        print(df_django['zoon_name'].drop_duplicates().shape)
        print(df_legacy['index'].drop_duplicates().shape)
