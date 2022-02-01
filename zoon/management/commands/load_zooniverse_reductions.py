import os
import ast
import json
import pandas as pd
from sqlalchemy import create_engine

from django.core.management.base import BaseCommand
from django.conf import settings

from zoon.models import ReducedResponse_Question, ReducedResponse_Text
from zoon.utils.zooniverse_config import parse_config_yaml


class Command(BaseCommand):
    '''Bulk load raw Zooniverse export data for further processing'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str, help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def find_best_answer(self, column_name, answer_lookup):
        '''Find out which answer for this particular task has the most votes'''
        return answer_lookup[column_name]

    def round_user_ids(self, input):
        '''Not sure if .0s at the end of user_ids are a product of being opened or Excel or a Zoom thing, but trimming them to ints, with -1 for None values'''
        return json.dumps([int(u) for u in json.loads(input.replace('nan', '-1'))])

    def jsonify(self, input):
        '''json.loads doesn't play nice with the output from Zooniverse from TEXT reducers, possibly because of single quotes. Those are hard to replace without killing apostrophes, so we're using literal_eval'''
        return json.dumps(ast.literal_eval(input))

    def join_answers(self, row):
        '''For dropdown reductions. Get rid of hashes for choices, and restructure slightly so the results can be sorted in descending order by number of votes for that answer'''

        values = json.loads(row['data.value'].replace("'", '"'))
        joined = []
        for v in values:
            for key, value in v.items():
                joined.append({'choice': row['options'][key], 'votes': value})

        return sorted(joined, key = lambda i: i['votes'], reverse=True)

    def load_questions_reduced(self, batch_dir: str, master_config: dict):
        '''Process reduced responses from the question reducer
        Arguments:
            batch_dir: Path to the export files for this batch
            master_config: Question text and label lookup object
        '''

        df = pd.read_csv(os.path.join(batch_dir, 'question_reducer_questions.csv'))
        config_df = pd.DataFrame(master_config)

        # Join responses to config so we know the possible answers to each question
        df = df.merge(
            config_df,
            how="left",
            left_on="task",
            right_on="task_num"
        )

        # Find all possible answers in the spreadsheet for all questions
        all_task_answer_cols = []
        for columns in df['answer_columns'].drop_duplicates().tolist():
            all_task_answer_cols += columns

        # Drop all rows from df with no answers for any of the possible questions. Not sure if this happens or not.
        df = df.dropna(subset=all_task_answer_cols, how='all')

        # Each question-type task will have a unique set of answer columns, all in the same spreadsheet. So we loop through each questions to grab the correct columns and data about which answer won.
        for task_num in df['task_num'].drop_duplicates().to_list():
            answer_columns = df[df['task_num'] == task_num]['answer_columns'].values[0]

            answers = df[df['task_num'] == task_num]['answers'].values[0]
            answers_lookup = {answer['value_column']: answer['value'] for answer in answers}

            df.loc[df['task_num'] == task_num, 'best_answer_column'] = df[answer_columns].idxmax(axis=1)

            df.loc[df['task_num'] == task_num, 'best_answer_score'] = df[answer_columns].max(axis=1)

            df.loc[df['task_num'] == task_num, 'best_answer'] = df['best_answer_column'].apply(lambda x: self.find_best_answer(x, answers_lookup))

            df.loc[df['task_num'] == task_num, 'total_votes'] = df[answer_columns].sum(axis=1)

            df.loc[df['task_num'] == task_num, 'answer_scores'] = df[answer_columns].to_json(orient='records', lines=True).splitlines()

        df = df.rename(columns={
            'subject_id': 'zoon_subject_id',
            'workflow_id': 'zoon_workflow_id',
            'task': 'task_id'
        })[[
            'zoon_subject_id',
            'zoon_workflow_id',
            'task_id',
            'best_answer',
            'best_answer_score',
            'total_votes',
            'answer_scores',
        ]]
        df['question_type'] = 'q'

        print(df)

        print('Sending reducer QUESTION results to Django ...')
        sa_engine = create_engine(settings.SQL_ALCHEMY_DB_CONNECTION_URL)
        df.to_sql('zoon_reducedresponse_question', if_exists='append', index=False, con=sa_engine)

    def load_dropdowns_reduced(self, batch_dir: str, master_config: dict):
        '''Process reduced responses from the dropdown reducer. In at least some versions, you need to look up hashes for fields.
        Example: [{'adbad85a7b5ce': 1, '2b3caf88e1ee6': 2}] (In this case, 1 person chose the first, 2 people the second)

        Arguments:
            batch_dir: Path to the export files for this batch
            master_config: Question text and label lookup object
        '''

        df = pd.read_csv(os.path.join(batch_dir, 'dropdown_reducer_dropdowns.csv'))
        config_df = pd.DataFrame(master_config)

        # Join responses to config so we know the possible answers to each question
        df = df.merge(
            config_df,
            how="left",
            left_on="task",
            right_on="task_num"
        )

        # Drop all rows from df with no answers.
        df = df.dropna(subset=['data.value'], how='all')

        df['answer_scores'] = df.apply(lambda row: self.join_answers(row), axis=1)
        df['best_answer'] = df['answer_scores'].apply(lambda x: x[0]['choice'])
        df['best_answer_score'] = df['answer_scores'].apply(lambda x: x[0]['votes'])
        df['total_votes'] = df['answer_scores'].apply(lambda x: sum([r['votes'] for r in x]))

        df = df.rename(columns={
            'subject_id': 'zoon_subject_id',
            'workflow_id': 'zoon_workflow_id',
            'task': 'task_id'
        })[[
            'zoon_subject_id',
            'zoon_workflow_id',
            'task_id',
            'best_answer',
            'best_answer_score',
            'total_votes',
            'answer_scores',
        ]]
        df['question_type'] = 'd'
        df['answer_scores'] = df['answer_scores'].apply(lambda x: json.dumps(x))

        print(df)

        print('Sending reducer DROPDOWN results to Django ...')
        sa_engine = create_engine(settings.SQL_ALCHEMY_DB_CONNECTION_URL)
        df.to_sql('zoon_reducedresponse_question', if_exists='append', index=False, con=sa_engine)

    def load_texts_reduced(self, batch_dir: str, master_config: dict):
        df = pd.read_csv(os.path.join(batch_dir, 'text_reducer_texts.csv'))
        config_df = pd.DataFrame(master_config)

        # We're not really doing anything with the config data for text-type questions, but just to maintain parallel structure...
        df = df.merge(
            config_df,
            how="left",
            left_on="task",
            right_on="task_num"
        )

        df.columns = df.columns.str.replace("data.", "", regex=False)

        # Drop all rows from df with no text input.
        df = df.dropna(subset=['aligned_text', 'consensus_text'], how='all')

        # Parse user_ids as int to drop weirdo .zero
        df['user_ids'] = df['user_ids'].apply(lambda x: self.round_user_ids(x))
        df['aligned_text'] = df['aligned_text'].apply(lambda x: self.jsonify(x))

        df = df.rename(columns={
            'subject_id': 'zoon_subject_id',
            'workflow_id': 'zoon_workflow_id',
            'task': 'task_id',
            'number_views': 'total_votes',
        })[[
            'zoon_subject_id',
            'zoon_workflow_id',
            'task_id',
            'aligned_text',
            'total_votes',
            'consensus_text',
            'consensus_score',
            'user_ids',
        ]]

        print(df)

        print('Sending reducer TEXT results to Django ...')
        sa_engine = create_engine(settings.SQL_ALCHEMY_DB_CONNECTION_URL)
        df.to_sql('zoon_reducedresponse_text', if_exists='append', index=False, con=sa_engine)

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:
            self.batch_config = settings.ZOONIVERSE_QUESTION_LOOKUP[workflow_name]
            self.batch_dir = os.path.join(settings.BASE_DIR, 'data', 'zooniverse_exports', self.batch_config['panoptes_folder'])

            self.config_yaml = os.path.join(self.batch_dir, self.batch_config['config_yaml'])

            master_config = parse_config_yaml(self.config_yaml)

            self.load_questions_reduced(self.batch_dir, master_config)
            self.load_dropdowns_reduced(self.batch_dir, master_config)
            self.load_texts_reduced(self.batch_dir, master_config)
