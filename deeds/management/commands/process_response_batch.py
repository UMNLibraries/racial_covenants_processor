import pandas as pd

# from deeds.models import ZooniverseResponseRaw
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    '''Processes normalized Zooniverse responses to extract real-estate fields and calculate reliability scores. Process brought into the Django world, but based on work by Kevin Ehrman and StarEightyTwo'''

    def handle(self, *args, **kwargs):
        # TODO PART I: Normalize Zooniverse export
        # Get only the workflow you want
        batch = 'Ramsey County'


        # #import zooniverse export
        # data = pandas.read_csv('E:/Mapping Prejudice/Zooniverse/Ramsey/exports/mapping-prejudice-classifications_2_17_2021.csv', header=None)
        #
        # #isolate workflow
        # data = data[data.iloc[:, 5] == 'Ramsey County']
        #
        # #isolate annotations column
        # data_anno = data.iloc[:, 11].map(json.loads)
        # datalist = data_anno.tolist()
        #
        # #isolate subject data column
        # data_subject = data.iloc[:, 12].map(json.loads)
        #
        #
        # #----------This section isolates all the relevent columns---------
        #
        # #deal with non-nested fields first
        # class_num = data[0].tolist()
        # user_list = data[1].tolist()
        # class_date_list = data[7].tolist()
        #
        # #deal the annotation field values
        # match_list = anno_list(0)
        # restriction_list = anno_list(1)
        # block_list = anno_list(3)
        # lot_list = anno_list(2)
        # addition_list = anno_list(4)
        #
        # #deal with the date
        # date_list_cleaned = date_list(5)
        #
        # #get subject metadata field values
        # subject_name = subject_metadata('default_frame')
        # retired_list = retired()
        #
        # #----------------put all the columns back together
        # #--------------------Stack lists and import to dataframe-------------------
        # print("Merge fields and print to CSV")
        #
        # date_str = date.today().strftime("%m_%d_%y")
        #
        # df_stack = pandas.DataFrame(numpy.column_stack([class_num, user_list, class_date_list, match_list, restriction_list, block_list, lot_list, addition_list, date_list_cleaned, subject_name, retired_list]),
        #                                columns=['Class_ID', 'User_Name', 'Class_Date', 'Match', 'Restriction', 'Block', 'Lot', 'Addition', 'Date', 'Image_ID', 'Retired' ])
        #
        # df_stack.to_csv('E:/Mapping Prejudice/Zooniverse/Ramsey/Intermediate/placeholder_' + date_str + '.csv', index=False, encoding='utf-8')


        # TODO: PART II: User_Rank

        # TODO PART III: Calculate Mode

        # TODO PART IV: Append and strip 'No' values
