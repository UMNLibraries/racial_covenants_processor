import os
import re
import datetime
import pandas as pd

from django.core.management.base import BaseCommand
from django.core.files.base import File
from django.db.models import Q, F
from django.conf import settings

from apps.zoon.models import ZooniverseSubject, ZooniverseWorkflow, ManualParcelPINLink
from apps.parcel.models import Parcel
from apps.zoon.utils.zooniverse_config import get_workflow_obj


class Command(BaseCommand):
    '''geojson exporter to either s3 or local file'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')
        parser.add_argument('-i', '--infile', type=str,
                            help='Path to document with pk values filled in and verified')
        
    def get_existing_manual_combos(self, workflow):
        # Get a list of what ManualParcelPINLink combos already exist to avoid duplication
        mppl_combos = pd.DataFrame(ManualParcelPINLink.objects.filter(
            workflow=workflow
        ).values(
            'zoon_subject_id',
            'parcel_pin'
        ))
        print(f"Found {mppl_combos.shape[0]} existing mppl_combos.")
       
        return mppl_combos


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

        infile = kwargs['infile']
        if not infile:
            print('Missing infile. Please specify with --infile.')
        else:
            df = pd.read_csv(infile)
            if 'verified?' not in df.columns:
                print("This CSV doesn't look right.")
                return False
            
        good_rows = df[(df['verified?'] == 'Yes') & (~df['parcel_pks'].isna())]

        parcel_df = good_rows.copy()[['id', 'zoon_subject_id', 'parcel_pks']]
        parcel_df['parcel_pk_list'] = parcel_df['parcel_pks'].str.split(', ')
        # Explode the 'parcel_pk_list' column to create new rows for each item
        exploded_parcel_df = parcel_df.explode('parcel_pk_list')
        exploded_parcel_df.rename(columns={"parcel_pk_list": "parcel_pk_single"}, inplace=True)
        exploded_parcel_df["parcel_pk_single"] = exploded_parcel_df["parcel_pk_single"].astype(int)

        # Build a df of matching Parcel records that are actually in this workflow
        parcel_pks_cands = exploded_parcel_df['parcel_pk_single'].drop_duplicates().to_list()
        true_parcels_df = pd.DataFrame(Parcel.objects.filter(
            workflow=workflow,
            pk__in=parcel_pks_cands
        ).values('pk', 'pin_primary'))
        print(f"Found {true_parcels_df.shape[0]} rows in CSV.")
        print(true_parcels_df)

        # Left join on goodexploded_parcel_df_rows to get df to create pin links
        final_df = exploded_parcel_df.merge(
            true_parcels_df,
            how="left",
            left_on="parcel_pk_single",
            right_on="pk"
        )
        final_df = final_df[~final_df['pin_primary'].isna()]
        print(f"Found {final_df.shape[0]} exploded rows to create.")
        print(final_df)

        # TODO: Check if these combos already exist since some have already run
        existing_df = self.get_existing_manual_combos(workflow)
        final_df = final_df.merge(
            existing_df,
            how='left',
            left_on=['zoon_subject_id', 'pin_primary'],
            right_on=['zoon_subject_id', 'parcel_pin'],
            indicator=True
        ).loc[lambda df: df['_merge'].eq('left_only')]

        print(f"Found {final_df.shape[0]} ManualParcelPINLink rows that still need to be created.")
        print(final_df)

        for row_num, p_row in final_df.iterrows():
            pin_link = ManualParcelPINLink(
                workflow=workflow,
                zooniverse_subject_id=p_row['id'],
                parcel_pin=p_row['pin_primary']
            )
            print(f"Saving manual parcel pin link for {p_row['id']}...")
            pin_link.save()
