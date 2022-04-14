import os
import datetime
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sklearn.metrics import cohen_kappa_score

from apps.deed.models import Workflow, ZooniverseResponseFlat, ZooniverseUser, ZooniverseUserRating
from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings

class Command(BaseCommand):
    '''Processes normalized Zooniverse responses to extract real-estate fields and calculate reliability scores. Process brought into the Django world, but based on work by Kevin Ehrman and StarEightyTwo'''

    def add_arguments(self, parser):
        parser.add_argument('-w', '--workflow', type=str, help='Name of Zooniverse workflow to process, e.g. "Ramsey County"')

    def handle_zero_division(self, x, y):
        try:
            return x/y
        except ZeroDivisionError:
            return None

    def handle(self, *args, **kwargs):
        workflow_name = kwargs['workflow']
        if not workflow_name:
            print('Missing workflow name. Please specify with --workflow.')
        else:

            #-------------------------------------------------------------------
            #----------------------PART II: User_Rank---------------------------
            #-------------------------------------------------------------------

            '''
            StarEightyTwo and Mapping Prejudice

            Reliability score calculation script
            v1.0
            11/26/2017

            This script takes the output from Kevin's
            current "cleaning" script - a "placeholder" CSV file -
            and outputs "reliability" scores for each
            volunteer. The reliability score for a given
            volunteer is the average of the Cohen's Kappa
            scores between that volunteer and every other
            volunteer multiplied by the log of the number
            of classifications completed by that user. The scale
            of the reliability score is fairly meaningless; the
            score is meant to be used to rank raters, not really
            for deep interpretation.

            Dependencies:

            Without getting too specific, this script
            should work with most versions of numpy, pandas,
            and scikit-learn. It is highly recommended that
            you run Python >= 3.x and not Python 2.x.
            '''

            qs = ZooniverseResponseFlat.objects.filter(
                workflow__workflow_name=workflow_name,
                dt_retired__isnull=False
            ).values('subject__id', 'user__id', 'bool_covenant', 'dt_created')
            df = pd.DataFrame(qs)

            # Matching original script names to reduce rewriting
            df.rename(columns={
                'subject__id': 'Image_ID',
                'bool_covenant': 'Match',
                'dt_created': 'Class_Date',
                'user__id': 'User_Name'  # Yes I know it's not the name but this makes DB joining easier and is functionally the same
            }, inplace=True)

            # Tweak "match" indicators so it's not booleans and nulls
            df.loc[df['Match'].isna(), 'Match'] = '?'
            df.loc[df['Match'] == True, 'Match'] = 'Yes'
            df.loc[df['Match'] == False, 'Match'] = 'No'

            df['User_Name'] = df['User_Name'].astype(int)
            df['Class_Date'] = pd.to_datetime(df['Class_Date'])

            # drop strange blank rows --- need to find a better solution for this, and also figure out how they are happening in the first place
            df['Match'].replace('', np.nan, inplace=True)
            df.dropna(subset=['Match'], inplace=True)

            # In the case of a user having seen an image more than once,
            # take their most recent answer.
            df = (df.sort_values('Class_Date', ascending=False)
                 .drop_duplicates(subset=['User_Name', 'Image_ID']))

            # Master list which will store information
            # calculated below
            reliability_data = []

            # Create groupby object to iterate through below
            gb = df.groupby('User_Name')

            # MJC: This loop pattern is probably slow compared to array-type operations but not going to work on rewriting it for now.
            # For each volunteer ("user" == "volunteer")
            for user, user_df in gb:

                # Images the main volunteer has seen and associated ratings
                user_img_seen = dict(zip(user_df['Image_ID'], user_df['Match']))

                # Create another groupby object for every other volunteer
                other_gb = df[df['User_Name'] != user].groupby('User_Name')

                # For every other user... You will want to automatically filter out
                # trolls/unreliable raters you find as you go along.. I think this is
                # part of the cleaning script currently.
                for other_user, other_df in other_gb:

                    # Images the other volunteer has seen and associated ratings
                    other_user_img_seen = dict(zip(other_df['Image_ID'], other_df['Match']))

                    # Set intersection between what the volunteer's
                    # seen and what the other volunteer has seen
                    common = set(user_img_seen) & set(other_user_img_seen)

                    # We only care to measure agreement between
                    # raters who have seen the same deeds
                    if common:
                        # Pairs of answers for each deed (image) commonly seen
                        together = [(user_img_seen[img], other_user_img_seen[img])
                                        for img in common]

                        # Used to calculate Cohen's Kappa...
                        # Just lists of each user's answers for all deeds shared
                        user_vector = [x[0] for x in together]
                        other_user_vector = [x[1] for x in together]
                        # If cohen_kappa_score returns np.nan, then we know each user agreed 100%...
                        # but there was no "random chance" component

                        # https://github.com/scikit-learn/scikit-learn/issues/9624
                        # "1 in Cohen's Kappa indicates perfect agreement
                        # with 0 chance of agreement at random.
                        # Here there is perfect agreement at random."

                        # Cohen's Kappa can also be zero when one rater
                        # gives the same answer for every subject
                        # (e.g. in the case) of a "no" troll
                        # print(user_vector, other_user_vector)
                        # cohen_kappa = cohen_kappa_score(user_vector, other_user_vector)
                        if len(set(user_vector).union(other_user_vector)) == 1:
                            cohen_kappa = np.nan
                        else:
                            cohen_kappa = cohen_kappa_score(user_vector, other_user_vector)
                            print(cohen_kappa)

                        # If we were able to calculate a kappa value
                        if not np.isnan(cohen_kappa):

                            # Sets of IDs agreed- and disagreed-upon
                            agreements = {img for img in common
                                          if user_img_seen[img] == other_user_img_seen[img]}

                            disagreements = {img for img in common
                                             if user_img_seen[img] != other_user_img_seen[img]}

                            # Number of images in common, agreed-upon, and disagreed-upon
                            n_common = len(common)
                            n_agreements = len(agreements)
                            n_disagreements = len(disagreements)

            				# Data to keep... JSON-style
                            reliability_data.append(
                                {
                                'user': user,
                                'other_user': other_user,
                                'cohen_kappa': cohen_kappa,
                                'n_in_common': n_common,
                                'user_together_drop_dupe': frozenset((user, other_user)),

                                # The following are relatively more naive measures of reliability...
                                'n_agreements': n_agreements,
                                'n_disagreements': n_disagreements,
                                'perc_agreements': self.handle_zero_division(n_agreements, n_common),
                                'perc_disagreements': self.handle_zero_division(n_disagreements, n_common),
                                'agree_disagree_ratio': self.handle_zero_division(n_agreements, n_disagreements)
                                }
                            )

            # Create a dataframe out of the information collected above
            agreement_df = pd.DataFrame.from_records(reliability_data)
            print(agreement_df)

            # Obtain the average Kappa score for each user
            # this is an average of the kappa between a given user and every user with whom
            # they shared images and disagreed at least once
            # Median is a bad measure, here, because of the usual skewness
            # of this distribution, so let's use mean
            avg_kappa = agreement_df.groupby(['user'])['cohen_kappa'].mean()
            print(avg_kappa)

            # Number of classifications for each user
            # this is used to develop the final reliability score later on
            num_clfs = df.groupby(['User_Name']).size().to_frame('n_clfs')
            print(num_clfs)

            # Put together the number of classifications and Cohen's Kappa values for each user
            reliability_df = pd.concat((avg_kappa, num_clfs), axis=1)

            # Product of each user's Cohen's Kappa score and the log of the number of classifications completed
            # There are diminishing "returns" to an increasing number of shared images...
            # The effect will always be positive, but incremental gains early on are much more rewarding than later on
            reliability_df['reliability_score'] = reliability_df['cohen_kappa'] * np.log(reliability_df['n_clfs'])

            # Rank the reliability scores. This isn't explicitly used, but might be valuable someday...
            reliability_df['rank'] = reliability_df['reliability_score'].rank(ascending=False)

            # Identify and flag raters in the
            # bottom 20% in terms of reliability...
            # could also look at bottom tail of distribution
            # of reliability scores... raters significantly
            # (i.e. 1-2 stddevs) below "normal"
            n_raters = reliability_df.shape[0]
            perc = 0.2
            cutoff = n_raters * (1-perc)
            bottom_percent_ranks = {i for i in reliability_df['rank'] if i >= cutoff}

            #reliability_df['bottom_percent'] = np.where(reliability_df.isin(bottom_percent_ranks), True, False)

            # Save the results with a unique (daily) identifier
            # session_id = "_".join(map(str, time.localtime()[:3]))
            # fname = 'reliability_scores_{}.csv'.format(session_id)

            timestamp = datetime.datetime.now().strftime('%Y%m%d')
            user_score_csv = os.path.join(settings.BASE_DIR, 'data', 'zooniverse_exports', f'reliability_scores_{timestamp}.csv')

            reliability_df = reliability_df.reset_index(drop=False)

            # MJC convert dataframe to Django objects
            sa_engine = create_engine(settings.SQL_ALCHEMY_DB_CONNECTION_URL)

            workflow = Workflow.objects.get(workflow_name=workflow_name)
            print('Deleting old user ratings for this workflow...')
            ZooniverseUserRating.objects.filter(workflow=workflow).delete()

            print('Sending new user ratings to Django ...')
            reliability_df['workflow_id'] = workflow.id

            pre_django_df = reliability_df.rename(columns={
                'index': 'user_id'
            }).to_sql('deeds_zooniverseuserrating', if_exists='append', index=False, con=sa_engine)

            # MJC: Get usernames from DB and join back
            # users_qs = pd.DataFrame(ZooniverseUser.objects.all().values('id', 'zoon_id', 'zoon_name')).rename(columns={'id': 'db_id'})
            # reliability_df = reliability_df.merge(
            #     users_qs,
            #     how="left",
            #     left_on="index",
            #     right_on="db_id"
            # ).drop(columns=['index'])
            #
            # reliability_df.to_csv(user_score_csv, index=False)
