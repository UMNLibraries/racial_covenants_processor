import os
import datetime
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sklearn.metrics import cohen_kappa_score

# import pandas as pd
from statistics import mode, StatisticsError
# from datetime import date

from deeds.models import Workflow, ZooniverseResponseFlat, ZooniverseUser, ZooniverseUserRating
from django.db.models import F
from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings

class Command(BaseCommand):
    '''TK TK'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str, help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def rev_sorted(a):
        '''Basically a wrapper to pass `reverse` argument using df.apply'''
        return sorted(a, reverse=True)

    def top_n_raters(a, n=2):
        '''Grab first n elements from iterable'''
        return a[:n]

    def rating_ratio(a):
        '''Used to find the reliability score ratio between two raters...

        returns None if only one rater available... don\'t need
        to investigate the Nones since there was only one rater'''
        try:
            return a[0]/a[1]
        except IndexError:
            return None

    def iter_until(answers, ranks, answer_limit={'Yes', 'No'}, rank_limit=1000):
        '''Iterate through list of answers and ranks to find satisfactory answer

        Example:
            >>> answers = ["I can't figure this one out.", 'Yes']
            >>> rater_ranks = [1, 23]
            >>> iter_until(answers, rater_ranks)
            {'answer': 'Yes', 'index': 1, 'rank': 23}
        '''
        if not all(isinstance(x, (list, tuple)) for x in [answers, ranks]):
            raise ValueError('Convert `answers` and `rank` to list or tuple')

        together = list(zip(answers, ranks))

        curr_val, curr_rank = together[0]
        next_idx = 1

        while curr_val not in answer_limit and curr_rank < rank_limit:
            try:
                curr_val, curr_rank = together[next_idx]
                next_idx += 1
                could_not_find_flag = False
            except IndexError:
                could_not_find_flag = True
                break
        data = {'next_best_answer': curr_val, 'next_best_rank': curr_rank,
                'index': next_idx-1, 'could_not_find_flag': could_not_find_flag}
        return data

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:

            #-------------------------------------------------------------------
            #----------------------PART III: Calculate Mode---------------------
            #-------------------------------------------------------------------

            # Get ratings and their users' reliablity score, dropping entries from users with a reliablity score below 1
            ratings = ZooniverseResponseFlat.objects.filter(
                workflow__workflow_name=workflow_name,
                dt_retired__isnull=False
            ).annotate(
                reliability_score=F('user__zooniverseuserrating__reliability_score')
            ).exclude(reliability_score__lt=1)

            print(ratings.values())

            # NOte stopping here for the moment.

            # idk_val = "I can't figure this one out."
            #
            # # The values will be one in the case of raters' sharing
            # # an identical reliability score... Or in the case of a rater
            # # seeing the same image twice (and thus being seen as two different raters)
            # # Use this as a reference to give power back to raters not as proflific
            # # if the ratio is high, trust the higher rater, but if the ratio's low,
            # # then two raters with similar reliabilities are asking to be looked at further
            # gb = (df.groupby('Image_ID')['reliability_score']
            #      .apply(rev_sorted)
            #      .apply(top_n_raters)
            #      .apply(rating_ratio))
            #
            #
            # # For each retired deed
            # def main_calc (field, catchlist_name):
            #     print('main field calc' + str(field))
            #     df_group = df.groupby('Image_ID')
            #     for img_id, frame in df_group:
            #         mode_val = frame['Match'].mode()
            #         sub_list = []
            #         for index, i in enumerate(frame['Match']):
            #             if i == mode_val[0]:
            #                 sub_list.append(frame.iloc[index])
            #             else:
            #                 pass
            #         sub_list_df = pd.DataFrame(sub_list)
            #         df_group_2 = sub_list_df.groupby('Image_ID')
            #         for img_id, frame in df_group_2:
            #             try:
            #                 mode_val = mode(frame[field])
            #                 catchlist_name.append({
            #                     'img_id': img_id,
            #                     field: mode_val,
            #                 })
            #                 # a StatisticsError exception will be raised when
            #                 # math.mode can't calculate mode
            #             except StatisticsError:
            #                     # Order the match choices based on rater reliability
            #                 frame.sort_values('reliability_score',
            #                                   ascending=False,
            #                                   inplace=True)
            #                 mode_val = frame[field].values[0]
            #                 row_data = {}
            #                 more_data = {
            #                     'img_id': img_id,
            #                     field : mode_val,
            #                     }
            #
            #                 row_data = {**row_data, **more_data}
            #
            #                 catchlist_name.append(row_data)
            #
            # retired_list = []
            # main_calc('Retired', retired_list)
            # retired_frame = pd.DataFrame.from_records(retired_list)
            #
            # user_name_list = []
            # main_calc('User_Name', user_name_list)
            # user_name_frame = pd.DataFrame.from_records(user_name_list)
            #
            # class_id_list = []
            # main_calc('Class_ID', class_id_list)
            # class_id_frame = pd.DataFrame.from_records(class_id_list)
            #
            # class_date_list = []
            # main_calc('Class_Date', class_date_list)
            # class_date_frame = pd.DataFrame.from_records(class_date_list)
            #
            # match_list = []
            # main_calc('Match', match_list)
            # match_frame = pd.DataFrame.from_records(match_list)
            #
            # racial_res_list = []
            # main_calc('Restriction', racial_res_list)
            # racial_res_frame = pd.DataFrame.from_records(racial_res_list)
            #
            # addition_value_list = []
            # main_calc('Addition', addition_value_list)
            # addition_value_frame = pd.DataFrame.from_records(addition_value_list)
            #
            # # city_list = []
            # # main_calc('City', city_list)
            # # city_frame = pd.DataFrame.from_records(city_list)
            #
            # lot_list = []
            # main_calc('Lot', lot_list)
            # lot_frame = pd.DataFrame.from_records(lot_list)
            #
            # block_list = []
            # main_calc('Block', block_list)
            # block_frame = pd.DataFrame.from_records(block_list)
            #
            # date_ex_list = []
            # main_calc('Date', date_ex_list)
            # date_ex_frame = pd.DataFrame.from_records(date_ex_list)
            #
            # reliability_score_list = []
            # main_calc('reliability_score', reliability_score_list)
            # reliability_score_frame = pd.DataFrame.from_records(reliability_score_list)
            #
            # rank_list = []
            # main_calc('rank', rank_list)
            # rank_frame = pd.DataFrame.from_records(rank_list)
            #
            #
            # # Attempt to join
            # join_final = (retired_frame.merge(user_name_frame, on="img_id").merge(reliability_score_frame, on="img_id")
            # .merge(rank_frame, on="img_id").merge(class_id_frame, on="img_id")
            # .merge(class_date_frame, on="img_id").merge(match_frame, on="img_id")
            # .merge(racial_res_frame, on="img_id").merge(addition_value_frame, on="img_id")
            # .merge(lot_frame, on="img_id").merge(block_frame, on="img_id")
            # .merge(date_ex_frame, on="img_id")
            # )
            #
            # print(join_final)
            # # join_final.to_csv('Intermediate\\' + 'mode_' + '8_28_2020' + '.csv',  index=False)
            #
            # # join_final.to_csv("E:\\Mapping Prejudice\\Zooniverse\\Ramsey\\Intermediate\\mode_2_17_2021.csv", index=False)
            # join_final.to_csv("/mnt/c/Users/corey101/Documents/code/racial_covenants_processor/racial_covenants_processor/data/zooniverse_exports/legacy/mode_01_25_2022.csv", index=False)
            #
            #
            #
            # # # My suggestion would be to look at the deeds
            # # # with small top_two_ratio values (meaning similar reliability between
            # # # raters) and idx_flag == True (i.e. "IDK" being the top answer, but clearly
            # # # not the only answer, since mode wasn't able to be calculated)
            # # # If someone with a high rank says "IDK" but someone with a
            # # # similar rank says "yes", maybe you take the "yes" instead of manually
            # # # reading the deed yourself...
            # #
            # #
            # # #-------------------------------------------------------------------
            # # #----------------------PART IV: Append and strip 'No' values--------
            # # #-------------------------------------------------------------------\
            # #
            # # df = join_final
            # #
            # # df_new = df
            # # df_old = pd.read_csv('E:\\Mapping Prejudice\\Zooniverse\\Ramsey\\Ramsey_Master_2_17_2021.csv')
            # # del_list = df_old.img_id.unique()
            # # df_new_unique = df_new[~df_new['img_id'].isin(del_list)]
            # #
            # # #remove 'no' rows from df_new_unique
            # # drop_list = ['No']
            # # df_new_unique_cleaned = df_new_unique[~df_new_unique['Match'].isin(drop_list)]
            # #
            # # merge_frames = [df_old, df_new_unique_cleaned]
            # # final_array = pd.concat(merge_frames)
            # #
            # # date_str = date.today().strftime("%m_%d_%y")
            # #
            # # final_array.to_csv('Master_CSV\\master_' + date_str + '.csv', index=False)
            #
            # # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            #
            # #Drop all raters that have a reliability score under 1.0
            # # df = df[df['reliability_score'].notnull()]
            # # df = df.query('reliability_score > 1')
            #
            # # print(ratings.filter(bool_covenant=True, reliability_score=None).values())
            # # # Read a placeholder file from part I
            # # # df = df = pd.read_csv('E:/Mapping Prejudice/Zooniverse/Ramsey/Intermediate/placeholder_02_17_21.csv', header=0)
            # # df = df = pd.read_csv('/mnt/c/Users/corey101/Documents/code/racial_covenants_processor/racial_covenants_processor/data/zooniverse_exports/legacy/placeholder_01_25_22.csv', header=0)
            # #
            # # # Consider only those images "retired"
            # # df = df[df['Retired'] == 'Retired']
            # #
            # # # Read in rater reliability ratings
            # # # ratings_df = pd.read_csv('E:/Mapping Prejudice/Zooniverse/Ramsey/Intermediate/reliability_scores_2021_2_17.csv')
            # # ratings_df = pd.read_csv('/mnt/c/Users/corey101/Documents/code/racial_covenants_processor/racial_covenants_processor/data/zooniverse_exports/legacy/reliability_scores_2022_1_25.csv')
            # #
            # #
            # #
            # # # Keep only those raters that have a reliability score
            # # ratings_df = ratings_df[ratings_df['reliability_score'].notnull()]
            # #
            # # # Join each rater's agreement index score with each image they've seen (each row)
            # # df = pd.merge(df, ratings_df,
            # #             left_on='User_Name',
            # #             right_on='index',
            # #             how='left')
            # #
            # # #Drop all raters that have a reliability score under 1.0
            # # df = df[df['reliability_score'].notnull()]
            # # df = df.query('reliability_score > 1')
            # #
