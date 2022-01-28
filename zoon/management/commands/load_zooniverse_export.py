import os
import pandas as pd
from sqlalchemy import create_engine

from django.core.management.base import BaseCommand
from django.conf import settings

from zoon.models import ReducedResponse_Question
from zoon.utils.zooniverse_config import parse_config_yaml


class Command(BaseCommand):
    '''Bulk load raw Zooniverse export data for further processing'''
    batch_config = None  # Set in handle

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str, help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def find_best_answer(self, column_name, answer_lookup):
        '''Find out which answer for this particular task has the most votes'''
        return answer_lookup[column_name]

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

        print(df)

        # print('Sending reducer QUESTION results to Django ...')
        # sa_engine = create_engine(settings.SQL_ALCHEMY_DB_CONNECTION_URL)
        # df.to_sql('zoon_reducedresponse_question', if_exists='append', index=False, con=sa_engine)


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
