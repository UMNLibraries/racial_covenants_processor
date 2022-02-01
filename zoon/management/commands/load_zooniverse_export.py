import os
import ast
import json
import datetime
import pandas as pd
from sqlalchemy import create_engine

from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings

from zoon.models import ZooniverseResponseRaw, ZooniverseWorkflow, ZooniverseSubject, ReducedResponse_Question, ReducedResponse_Text
from zoon.utils.zooniverse_config import parse_config_yaml


class Command(BaseCommand):
    '''This is the main loader for a Zooniverse export and set of reduced output into the Django app.'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str, help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def load_csv(self, infile: str):
        '''
        Implements a django-postgres-copy loader to bulk load raw Zooniverse responses into the ZooniverseResponseRaw model.

        Arguments:
            infile: path to raw classifications CSV
        '''
        print("Loading raw Zooniverse export data...")
        import_csv = os.path.join(settings.BASE_DIR, 'data', 'zooniverse_exports', 'mapping-prejudice-classifications_2_23_2021.csv')

        # Make custom mapping from model fields to drop IP column
        mapping = {f.name: f.name for f in ZooniverseResponseRaw._meta.get_fields() if f.name not in ['id', 'subject_data_flat', 'zooniverseresponseflat']}

        insert_count = ZooniverseResponseRaw.objects.from_csv(import_csv, mapping=mapping)
        print("{} records inserted".format(insert_count))

    def flatten_subject_data(self, workflow_name:str):
        '''
        The raw "subject_data" coming back from Zooniverse is a JSON object with the key of the "subject_id". The data being stored behind this key cannot easily be queried by Django, but if we flatten it, we can. This creates a flattened copy of the subject_data field to make querying easier, and updates the raw responses in bulk.
        '''
        print("Creating flattened version of subject_data...")
        responses = ZooniverseResponseRaw.objects.filter(workflow_name=workflow_name).only('subject_data')

        for response in responses:
            first_key = next(iter(response.subject_data))
            response.subject_data_flat = response.subject_data[first_key]

        ZooniverseResponseRaw.objects.bulk_update(responses, ['subject_data_flat'], 10000)  # Batches of 10,000 records at a time

    def clear_all_tables(self, workflow_name:str):
        print('WARNING: Clearing all tables before import...')

        ZooniverseResponseRaw.objects.filter(workflow_name=workflow_name).delete()
        ZooniverseSubject.objects.filter(workflow__workflow_name=workflow_name).delete()

    def create_workflow(self, workflow_name:str):
        # Check if this name exists in raw responses
        matches = ZooniverseResponseRaw.objects.filter(workflow_name=workflow_name).values('workflow_id').distinct()
        if matches.count() > 0:
            workflow, w_created = ZooniverseWorkflow.objects.get_or_create(
                zoon_id=matches[0]['workflow_id'],
                workflow_name=workflow_name
            )
            if w_created:
                print(f"New workflow record created for {workflow_name}.")
            else:
                print(f"Existing workflow record found for {workflow_name}.")
            return workflow
        else:
            print("No matching workflow found in Zooniverse responses.")
            raise

    def sql_df_writer(self, conn, var_name, question_lookup):
        '''Help pandas return a sensible response for each question that can be joined back to a unique subject id. Scores are put into percentages to handle possible changes to what's required to retire.'''
        return pd.read_sql(f"SELECT zoon_subject_id, best_answer AS {var_name}, cast(best_answer_score as float)/cast(total_votes as float) AS {var_name}_score FROM zoon_reducedresponse_question WHERE task_id = '{question_lookup[var_name]}'",
            conn)
        # , id AS {var_name}_reducer_db_id

    def sql_df_writer_text(self, conn, var_name, question_lookup):
        '''Help pandas return a sensible response for each question that can be joined back to a unique subject id. Scores are put into percentages to handle possible changes to what's required to retire.'''
        return pd.read_sql(f"SELECT zoon_subject_id, consensus_text AS {var_name}, cast(consensus_score as float)/cast(total_votes as float) AS {var_name}_score FROM zoon_reducedresponse_text WHERE task_id = '{question_lookup[var_name]}'",
            conn)
        # , id AS {var_name}_reducer_db_id

    def parse_deed_date(self, row, month_lookup):
        try:
            month = month_lookup[row['month']]
            return datetime.datetime(int(row['year']), month, int(row['day'])).date()
        except:
            return None

    def consolidate_responses(self, workflow, question_lookup: dict):
        print('Bring together reducer answers to a final results for this subject...')

        # Only get retired subjects
        subject_df = pd.DataFrame(ZooniverseResponseRaw.objects.filter(
            workflow_name=workflow.workflow_name
        ).exclude(
            subject_data_flat__retired=None  # Only loading retired subjects for now
        ).values(
            'subject_ids',
            'subject_data_flat__retired__retired_at'
        ).distinct())
        subject_df.rename(columns={
            'subject_ids': 'zoon_subject_id',
            'subject_data_flat__retired__retired_at': 'dt_retired'
        }, inplace=True)
        print(subject_df)

        sa_engine = create_engine(settings.SQL_ALCHEMY_DB_CONNECTION_URL)

        # Make a DF for each question, then left join to subject IDs to create subject records
        bool_covenant_df = self.sql_df_writer(sa_engine, 'bool_covenant', question_lookup)
        print(bool_covenant_df)
        covenant_text_df = self.sql_df_writer_text(sa_engine, 'covenant_text', question_lookup)
        addition_df = self.sql_df_writer_text(sa_engine, 'addition', question_lookup)
        lot_df = self.sql_df_writer_text(sa_engine, 'lot', question_lookup)
        block_df = self.sql_df_writer_text(sa_engine, 'block', question_lookup)
        seller_df = self.sql_df_writer_text(sa_engine, 'seller', question_lookup)
        buyer_df = self.sql_df_writer_text(sa_engine, 'buyer', question_lookup)

        # deed_date
        deed_date_year_df = self.sql_df_writer(sa_engine, 'year', question_lookup['deed_date'])
        deed_date_month_df = self.sql_df_writer(sa_engine, 'month', question_lookup['deed_date'])
        deed_date_day_df = self.sql_df_writer(sa_engine, 'day', question_lookup['deed_date'])

        # Join back to subject ids/retired dates
        final_df = subject_df.merge(
            bool_covenant_df, how="left", on="zoon_subject_id"
        ).merge(
            covenant_text_df, how="left", on="zoon_subject_id"
        ).merge(
            addition_df, how="left", on="zoon_subject_id"
        ).merge(
            lot_df, how="left", on="zoon_subject_id"
        ).merge(
            block_df, how="left", on="zoon_subject_id"
        ).merge(
            seller_df, how="left", on="zoon_subject_id"
        ).merge(
            buyer_df, how="left", on="zoon_subject_id"
        ).merge(
            deed_date_year_df, how="left", on="zoon_subject_id"
        ).merge(
            deed_date_month_df, how="left", on="zoon_subject_id"
        ).merge(
            deed_date_day_df, how="left", on="zoon_subject_id"
        )

        # Make overall and individual scores for deed date components
        final_df['deed_date_overall_score'] = final_df[['year_score', 'month_score', 'day_score']].sum(axis=1) / 3
        final_df.rename(columns={
            'year_score': 'deed_date_year_score',
            'month_score': 'deed_date_month_score',
            'day_score': 'deed_date_day_score',
        }, inplace=True)

        # Parse final deed_date
        month_lookup = question_lookup['month_lookup']
        final_df['deed_date'] = final_df.apply(lambda row: self.parse_deed_date(row, month_lookup), axis=1)

        # Parse bool_covenant and "I can't figure this out"
        final_df['bool_problem'] = False
        final_df.loc[final_df['bool_covenant'] == "I can't figure this one out", 'bool_problem'] = True
        final_df.loc[final_df['bool_covenant'] == "I can't figure this one out", 'bool_covenant'] = None
        final_df.loc[final_df['bool_covenant'] == "Yes", 'bool_covenant'] = True
        final_df.loc[final_df['bool_covenant'] == "No", 'bool_covenant'] = False

        # Fill NAs in text fields with empty strings
        string_fields = ['covenant_text', 'addition', 'lot', 'block', 'seller', 'buyer']
        final_df[string_fields] = final_df[string_fields].fillna('')

        final_df.drop(columns=['year', 'month', 'day'], inplace=True)
        final_df['workflow_id'] = workflow.id

        print(final_df[final_df['bool_covenant'] == 'Yes'])

        print('Sending consolidated subject results to Django ...')
        final_df.to_sql('zoon_zooniversesubject', if_exists='append', index=False, con=sa_engine)

        # TODO: Associate subject with reduced answers after the fact?
        # TODO: Associate raw zooniverse records to ZooniverseSubject

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            # This config info comes from local_settings, generally.
            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            self.batch_dir = os.path.join(settings.BASE_DIR, 'data', 'zooniverse_exports', self.batch_config['panoptes_folder'])

            raw_classifications_csv = os.path.join(self.batch_dir, self.batch_config['raw_classifications_csv'])

            question_lookup = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]

            self.clear_all_tables(workflow_name)
            self.load_csv(raw_classifications_csv)
            workflow = self.create_workflow(workflow_name)
            self.flatten_subject_data(workflow_name)

            # Handle reducer output to develop consensus answers
            management.call_command('load_zooniverse_reductions', workflow=workflow_name)

            # After you have loaded the zooniverse reducer output, bring everything together
            self.consolidate_responses(workflow, question_lookup)
            # TODO: self.check_import(workflow_name)
