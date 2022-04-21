import os
import re
import json
import datetime
import pandas as pd
from itertools import chain
from sqlalchemy import create_engine

from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings

from apps.zoon.models import ZooniverseResponseRaw, ZooniverseResponseProcessed, ZooniverseWorkflow, ZooniverseSubject, ReducedResponse_Question, ReducedResponse_Text
from apps.zoon.utils.zooniverse_config import get_workflow_version
from apps.parcel.utils.parcel_utils import write_join_strings


class Command(BaseCommand):
    '''This is the main loader for a Zooniverse export and set of reduced output into the Django app.'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str,
                            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def load_csv(self, infile: str):
        '''
        Implements a django-postgres-copy loader to bulk load raw Zooniverse responses into the ZooniverseResponseRaw model.

        Arguments:
            infile: path to raw classifications CSV
        '''
        print("Loading raw Zooniverse export data...")
      # import_csv = os.path.join(settings.BASE_DIR, 'data', 'zooniverse_exports',
      #                           'mapping-prejudice-classifications_2_23_2021.csv')

        # Make custom mapping from model fields to drop IP column
        mapping = {f.name: f.name for f in ZooniverseResponseRaw._meta.get_fields(
        ) if f.name not in ['id', 'subject_data_flat', 'subject', 'zooniverseresponseprocessed']}

        insert_count = ZooniverseResponseRaw.objects.from_csv(
            infile, mapping=mapping)
        print("{} records inserted".format(insert_count))

    def flatten_subject_data(self, workflow):
        '''
        The raw "subject_data" coming back from Zooniverse is a JSON object with the key of the "subject_id". The data being stored behind this key cannot easily be queried by Django, but if we flatten it, we can. This creates a flattened copy of the subject_data field to make querying easier, and updates the raw responses in bulk.
        '''
        print("Creating flattened version of subject_data...")
        responses = ZooniverseResponseRaw.objects.filter(
            workflow_name=workflow.workflow_name,
            workflow_version=workflow.version
        ).only('subject_data')

        for response in responses:
            first_key = next(iter(response.subject_data))
            response.subject_data_flat = response.subject_data[first_key]

            # In some workflows the key for the match number is just a number, which will throw off querying of it later, so fix that
            response.subject_data_flat = {re.sub(
                r'^(\d+)$', r'image_\1', key): value for key, value in response.subject_data_flat.items()}

        ZooniverseResponseRaw.objects.bulk_update(
            responses, ['subject_data_flat'], 10000)  # Batches of 10,000 records at a time

    def clear_all_tables(self, workflow_name: str):
        print('WARNING: Clearing all tables before import...')

        ZooniverseResponseRaw.objects.filter(
            workflow_name=workflow_name).delete()
        ZooniverseSubject.objects.filter(
            workflow__workflow_name=workflow_name).delete()
        ZooniverseResponseProcessed.objects.filter(
            workflow__workflow_name=workflow_name).delete()

        try:
            workflow = ZooniverseWorkflow.objects.get(
                workflow_name=workflow_name)

            ReducedResponse_Question.objects.filter(
                zoon_workflow_id=workflow.zoon_id
            ).delete()
            ReducedResponse_Text.objects.filter(
                zoon_workflow_id=workflow.zoon_id
            ).delete()
        except:
            print("Can't find matching workflow, deleting all orphaned reducer output")
            all_workflow_ids = ZooniverseWorkflow.objects.all().values('zoon_id').distinct()
            ReducedResponse_Question.objects.exclude(
                zoon_workflow_id__in=all_workflow_ids
            ).delete()
            ReducedResponse_Text.objects.exclude(
                zoon_workflow_id__in=all_workflow_ids
            ).delete()

    def create_workflow(self, workflow_name: str, workflow_version: str):
        # Check if this name exists in raw responses
        matches = ZooniverseResponseRaw.objects.filter(
            workflow_name=workflow_name).values('workflow_id').distinct()
        if matches.count() > 0:
            workflow, w_created = ZooniverseWorkflow.objects.get_or_create(
                zoon_id=matches[0]['workflow_id'],
                workflow_name=workflow_name,
                version=workflow_version
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
            workflow_name=workflow.workflow_name,
            workflow_version=workflow.version
        ).exclude(
            subject_data_flat__retired=None  # Only loading retired subjects for now
        ).values(
            'subject_ids',
            'subject_data_flat__retired__retired_at',
            'subject_data_flat__image_1',
            'subject_data_flat__image_2',
            'subject_data_flat__image_3',
            'subject_data_flat__image_4',
        ).distinct())

        # Make a list of image ids associated with this subject
        # This may or may not be a _match png, which is something we will want to standardize with an actual ID from the earlier stages of the process that will carry through Zooniverse for joining back
        image_cols = [
            'subject_data_flat__image_1',
            'subject_data_flat__image_2',
            'subject_data_flat__image_3',
            'subject_data_flat__image_4'
        ]
        subject_df['image_ids'] = subject_df[image_cols].values.tolist()
        subject_df['image_ids'] = subject_df['image_ids'].apply(
            lambda x: json.dumps(x))

        subject_df.drop(columns=image_cols, inplace=True)

        subject_df.rename(columns={
            'subject_ids': 'zoon_subject_id',
            'subject_data_flat__retired__retired_at': 'dt_retired',
        }, inplace=True)
        print(subject_df)

        sa_engine = create_engine(settings.SQL_ALCHEMY_DB_CONNECTION_URL)

        # Make a DF for each question, then left join to subject IDs to create subject records
        bool_covenant_df = self.sql_df_writer(
            sa_engine, 'bool_covenant', question_lookup)
        print(bool_covenant_df)
        covenant_text_df = self.sql_df_writer_text(
            sa_engine, 'covenant_text', question_lookup)
        addition_df = self.sql_df_writer_text(
            sa_engine, 'addition', question_lookup)
        lot_df = self.sql_df_writer_text(sa_engine, 'lot', question_lookup)
        block_df = self.sql_df_writer_text(sa_engine, 'block', question_lookup)
        seller_df = self.sql_df_writer_text(
            sa_engine, 'seller', question_lookup)
        buyer_df = self.sql_df_writer_text(sa_engine, 'buyer', question_lookup)

        # deed_date
        deed_date_year_df = self.sql_df_writer(
            sa_engine, 'year', question_lookup['deed_date'])
        deed_date_month_df = self.sql_df_writer(
            sa_engine, 'month', question_lookup['deed_date'])
        deed_date_day_df = self.sql_df_writer(
            sa_engine, 'day', question_lookup['deed_date'])

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
        final_df['deed_date_overall_score'] = final_df[[
            'year_score', 'month_score', 'day_score']].sum(axis=1) / 3
        final_df.rename(columns={
            'year_score': 'deed_date_year_score',
            'month_score': 'deed_date_month_score',
            'day_score': 'deed_date_day_score',
        }, inplace=True)

        # Calculate median score
        score_cols = [
            'bool_covenant_score',
            'covenant_text_score',
            'addition_score',
            'lot_score',
            'block_score',
            'seller_score',
            'buyer_score',
            'deed_date_year_score',
            'deed_date_month_score',
            'deed_date_day_score',
        ]
        final_df['median_score'] = final_df[score_cols].median(axis=1)

        # Parse final deed_date
        month_lookup = question_lookup['month_lookup']
        final_df['deed_date'] = final_df.apply(
            lambda row: self.parse_deed_date(row, month_lookup), axis=1)

        # Parse bool_covenant and "I can't figure this out"
        final_df['bool_problem'] = False
        final_df.loc[final_df['bool_covenant']
                     == "I can't figure this one out", 'bool_problem'] = True
        final_df.loc[final_df['bool_covenant']
                     == "I can't figure this one out", 'bool_covenant'] = None
        final_df.loc[final_df['bool_covenant']
                     == "Yes", 'bool_covenant'] = True
        final_df.loc[final_df['bool_covenant']
                     == "No", 'bool_covenant'] = False

        # Set beginning join_strings
        final_df['join_candidates'] = final_df.apply(
            self.get_join_candidates, axis=1)

        # Fill NAs in text fields with empty strings
        string_fields = ['covenant_text', 'addition',
                         'lot', 'block', 'seller', 'buyer']
        final_df[string_fields] = final_df[string_fields].fillna('')

        final_df.drop(columns=['year', 'month', 'day'], inplace=True)
        final_df['workflow_id'] = workflow.id

        print(final_df)

        print('Sending consolidated subject results to Django ...')
        final_df.to_sql('zoon_zooniversesubject',
                        if_exists='append', index=False, con=sa_engine)

    def get_join_candidates(self, row):
        return write_join_strings(row['addition'], row['block'], row['lot'])

    def anno_accessor(self, input_obj, q_id):
        try:
            return [a['value'] for a in input_obj if a['task'] == q_id][0]
        except:
            # Search for nested: Find a value that is a list
            nested_lists = [a['value']
                            for a in input_obj if type(a['value']) is list]
            combined_list = list(chain(*nested_lists))
            try:
                return [a['value'][0]['label']
                        for a in combined_list if a['task'] == q_id][0]
            except:
                return ''
        return ''

    def extract_individual_responses(self, workflow, question_lookup: dict):
        print(
            'Pulling individual responses out of annotations object for easier display...')

        subject_ids = pd.DataFrame(ZooniverseSubject.objects.filter(
            workflow=workflow
        ).values('id', 'zoon_subject_id')).rename(columns={'id': 'subject_id'})

        df = pd.DataFrame(ZooniverseResponseRaw.objects.filter(
            workflow_name=workflow.workflow_name
        ).exclude(
            subject_data_flat__retired=None  # Only loading retired subjects for now
        ).values(
            'id',
            'classification_id',
            'user_name',
            'user_id',
            'subject_ids',
            'created_at',
            'annotations'
        ))

        df = df.merge(
            subject_ids,
            how="left",
            left_on="subject_ids",
            right_on="zoon_subject_id"
        )

        df['workflow_id'] = workflow.id
        df = df.rename(columns={
            'id': 'response_raw_id'
        })

        df['bool_covenant'] = df['annotations'].apply(
            lambda x: self.anno_accessor(x, question_lookup['bool_covenant']))
        df['covenant_text'] = df['annotations'].apply(
            lambda x: self.anno_accessor(x, question_lookup['covenant_text']))
        df['addition'] = df['annotations'].apply(
            lambda x: self.anno_accessor(x, question_lookup['addition']))
        df['block'] = df['annotations'].apply(
            lambda x: self.anno_accessor(x, question_lookup['block']))
        df['lot'] = df['annotations'].apply(
            lambda x: self.anno_accessor(x, question_lookup['lot']))
        df['seller'] = df['annotations'].apply(
            lambda x: self.anno_accessor(x, question_lookup['seller']))
        df['buyer'] = df['annotations'].apply(
            lambda x: self.anno_accessor(x, question_lookup['buyer']))

        df['deed_date_year'] = df['annotations'].apply(
            lambda x: self.anno_accessor(x, question_lookup['deed_date']['year']))

        df['deed_date_month'] = df['annotations'].apply(
            lambda x: self.anno_accessor(x, question_lookup['deed_date']['month']))

        df['deed_date_day'] = df['annotations'].apply(
            lambda x: self.anno_accessor(x, question_lookup['deed_date']['day']))

        df = df.drop(columns=['annotations', 'subject_ids', 'zoon_subject_id'])

        print(df)

        print('Sending processed individual responses to Django ...')
        sa_engine = create_engine(settings.SQL_ALCHEMY_DB_CONNECTION_URL)
        df.to_sql('zoon_zooniverseresponseprocessed',
                  if_exists='append', index=False, con=sa_engine)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            # This config info comes from local_settings, generally.
            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            self.batch_dir = os.path.join(
                settings.BASE_DIR, 'data', 'zooniverse_exports', self.batch_config['panoptes_folder'])

            workflow_slug = workflow_name.lower().replace(" ", "-")

            raw_classifications_csv = os.path.join(
                self.batch_dir, f"{workflow_slug}-classifications.csv")

            # Get workflow version from config yaml
            workflow_version = get_workflow_version(
                self.batch_dir, self.batch_config['config_yaml'])

            self.clear_all_tables(workflow_name)
            self.load_csv(raw_classifications_csv)

            workflow = self.create_workflow(
                workflow_name, workflow_version)

            self.flatten_subject_data(workflow)

            # Handle reducer output to develop consensus answers
            management.call_command(
                'load_zooniverse_reductions', workflow=workflow_name)

            # After you have loaded the zooniverse reducer output, bring everything together
            self.consolidate_responses(
                workflow, self.batch_config['zooniverse_config'])
            self.extract_individual_responses(
                workflow, self.batch_config['zooniverse_config'])

            # Handle reducer output to develop consensus answers
            management.call_command(
                'connect_manual_corrections', workflow=workflow_name)
