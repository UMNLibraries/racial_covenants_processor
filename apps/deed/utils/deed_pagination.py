import numpy as np
import pandas as pd
from django.db.models import Count, OuterRef, Subquery, F, Q, Case, When, Value, ImageField

from apps.deed.models import DeedPage

def tag_doc_num_page_counts(df):
    page_counts = df[['doc_num', 'public_uuid']].groupby(['doc_num']).count().reset_index().rename(columns={'public_uuid': 'doc_page_count'})
    # page_counts = df[['doc_num']].value_counts().reset_index(names='doc_page_count')
    # print(page_counts)
    return df.merge(
        page_counts,
        how='left',
        on='doc_num'
    )

def pagination_merge(match_df, doc_list_df, doc_or_book_selector='doc_num', offset=1, split_page=False):
    split_str = ''
    if split_page:
        split_str = 'split_'

    if offset == -1:
        new_image_field = 'prev_page_image_web'
    elif offset == 1:
        new_image_field = 'next_page_image_web'
    elif offset == 2:
        new_image_field = 'next_next_page_image_web'

    match_df[f'{split_str}page_num_{offset}'] = match_df[f'{split_str}page_num'] + offset

    doc_list_copy = doc_list_df.copy().drop_duplicates()
    doc_list_copy[new_image_field] = doc_list_copy['page_image_web']
    doc_list_copy[f'{split_str}page_num_right'] = doc_list_copy[f'{split_str}page_num']
    doc_list_copy.drop(columns=['page_image_web', f'{split_str}page_num'])

    '''Problem here is caused by there being a splitpage page in the next and next-next positions. That's somewhat of an outlier, but it's also not even supposed to be hitting join 3 because it has a doc num in addition to book and page. Should just rely on doc num and page count to say no prev or next. Need to sort right side of join by doc_num/page_num/splitpage_num and drop duplicates on result on important fields'''

    match_df = match_df.merge(
        doc_list_copy[[
            doc_or_book_selector,
            f'{split_str}page_num_right',
            new_image_field
        ]],
        # doc_list_df.copy()[[
        #     doc_or_book_selector,
        #     f'{split_str}page_num',
        #     'page_image_web'
        # ]].rename(columns={
        #     'page_image_web': new_image_field,
        #     f'{split_str}page_num': f'{split_str}page_num_right'
        # }),
        how="left",
        left_on=[doc_or_book_selector, f"{split_str}page_num_{offset}"],
        right_on=[doc_or_book_selector, f"{split_str}page_num_right"]
    ).drop(columns=[f"{split_str}page_num_right"]).drop_duplicates(subset=['s3_lookup'])

    return match_df

def paginate_deedpage_df(df, matches_only=False):
    # TODO: Change page_num and split_page_num to ints
    df["page_num"] = pd.to_numeric(df["page_num"])
    df["split_page_num"] = pd.to_numeric(df["split_page_num"])

    if matches_only:
        match_df = df[df['bool_match'] == True].copy()
    else:
        match_df = df

    doc_list_df = df[[
        's3_lookup',
        'doc_num',
        'book_id',
        'page_num',
        'split_page_num',
        'page_image_web'
    ]].copy()

    # print('Join 1')
    # same doc num with multiple pages + splitpage
    doc_num_split_page_df = match_df[(match_df['doc_page_count'] > 1) & (match_df['split_page_num'] >= 1)].copy()

    for offset in [-1, 1, 2]:
        doc_num_split_page_df = pagination_merge(
            doc_num_split_page_df,
            doc_list_df,
            'doc_num',
            offset=offset,
            split_page=True
        )

    # print(doc_num_split_page_df)
    # doc_num_split_page_df.to_csv('test_join_1.csv')

    # print('Join 2')
    # no doc_num, book and page only, splitpage
    book_id_split_page_df = match_df[(match_df['doc_page_count'] == 1) & (match_df['split_page_num'] >= 1)].copy()

    for offset in [-1, 1, 2]:
        book_id_split_page_df = pagination_merge(
            book_id_split_page_df,
            doc_list_df,
            'book_id',
            offset=offset,
            split_page=True
        )

    # print(book_id_split_page_df)
    # book_id_split_page_df.to_csv('test_join_2.csv')

    # print('Join 3')
    # no doc_num, book and page only, no splitpage
    book_id_no_split_page_df = match_df[(match_df['book_id'] != '') & (match_df['doc_page_count'] == 1)].copy()

    for offset in [-1, 1, 2]:
        book_id_no_split_page_df = pagination_merge(
            book_id_no_split_page_df,
            doc_list_df,
            'book_id',
            offset=offset,
            split_page=False
        )

    # print(book_id_no_split_page_df)
    # book_id_no_split_page_df.to_csv('test_join_3.csv')

    # print('Join 4')
    # no doc_num, book and page only, no splitpage
    doc_num_one_page_df = match_df[(match_df['book_id'] == '') & (match_df['doc_page_count'] == 1)].copy()

    # Don't really need to join, it's just one page
    doc_num_one_page_df['prev_page_image_web'] = ''
    doc_num_one_page_df['next_page_image_web'] = ''
    doc_num_one_page_df['next_next_page_image_web'] = ''

    # print(book_id_no_split_page_df)
    # book_id_no_split_page_df.to_csv('test_join_4.csv')

    # print('Join 5')
    # doc_num, no splitpage (everything left over)
    already_matched_lookups = pd.concat([
        doc_num_split_page_df['s3_lookup'],
        book_id_split_page_df['s3_lookup'],
        book_id_no_split_page_df['s3_lookup'],
        doc_num_one_page_df['s3_lookup']
    ])

    doc_num_no_split_page_df = match_df[~match_df['s3_lookup'].isin(already_matched_lookups)].copy()

    for offset in [-1, 1, 2]:
        doc_num_no_split_page_df = pagination_merge(
            doc_num_no_split_page_df,
            doc_list_df,
            'doc_num',
            offset=offset,
            split_page=False
        )

    # print(doc_num_no_split_page_df)
    # doc_num_no_split_page_df.to_csv('test_join_5.csv')

    out_df = pd.concat([
        doc_num_split_page_df,
        book_id_split_page_df,
        book_id_no_split_page_df,
        doc_num_one_page_df,
        doc_num_no_split_page_df
    ]).copy()

    out_df[[
        'prev_page_image_web', 'next_page_image_web', 'next_next_page_image_web'
    ]].fillna(value='', inplace=True)

    # out_df.fillna(value='', inplace=True)
    out_df = out_df.replace([np.nan], [None])

    return out_df

def tag_prev_next_image_sql(workflow):

    print('Gathering doc list...')
    full_doc_list_df = pd.DataFrame(DeedPage.objects.filter(
        workflow=workflow
    ).values(
        'bool_match',
        'doc_num',
        'book_id',
        'doc_page_count',
        'page_num',
        'split_page_num',
        'page_image_web',
        's3_lookup'
    ))

    match_df = paginate_deedpage_df(full_doc_list_df)
    # print(match_df)
    # match_df.to_csv('final_concat.csv')

    matches_to_update = DeedPage.objects.filter(
        workflow=workflow,
        bool_match=True
    ).only('s3_lookup')

    update_objs = []

    for match in matches_to_update:

        df_rows = match_df[match_df['s3_lookup'] == match.s3_lookup].fillna(value='')
        match.prev_page_image_web = df_rows['prev_page_image_web'].iloc[0]
        match.next_page_image_web = df_rows['next_page_image_web'].iloc[0]
        match.next_next_page_image_web = df_rows['next_next_page_image_web'].iloc[0]

        update_objs.append(match)

    print("Updating db objects...")
    DeedPage.objects.bulk_update(update_objs, ['prev_page_image_web', 'next_page_image_web', 'next_next_page_image_web'], batch_size=100)
