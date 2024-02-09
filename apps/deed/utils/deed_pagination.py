import numpy as np
import pandas as pd
from django.db.models import Count, OuterRef, Subquery, F, Q, Case, When, Value, ImageField
from django.db import connection

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
        new_image_lookup_field = 'prev_page_image_lookup'
    elif offset == 1:
        new_image_field = 'next_page_image_web'
        new_image_lookup_field = 'next_page_image_lookup'
    elif offset == 2:
        new_image_field = 'next_next_page_image_web'
        new_image_lookup_field = 'next_next_page_image_lookup'

    match_df[f'{split_str}page_num_{offset}'] = match_df[f'{split_str}page_num'] + offset

    # doc_list_copy = doc_list_df.copy()
    # Rather than making a copy here, why not just keep changing/adding values for lookup purposes, and drop unwanted columns when merging
    doc_list_df[new_image_field] = doc_list_df['page_image_web']
    doc_list_df[new_image_lookup_field] = doc_list_df['s3_lookup']
    doc_list_df[f'{split_str}page_num_right'] = doc_list_df[f'{split_str}page_num']
    # doc_list_copy.drop(columns=['page_image_web', f'{split_str}page_num'])

    '''Problem here is caused by there being a splitpage page in the next and next-next positions. That's somewhat of an outlier, but it's also not even supposed to be hitting join 3 because it has a doc num in addition to book and page. Should just rely on doc num and page count to say no prev or next. Need to sort right side of join by doc_num/page_num/splitpage_num and drop duplicates on result on important fields'''

    match_df = match_df.merge(
        doc_list_df[[
            doc_or_book_selector,
            f'{split_str}page_num_right',
            new_image_field,
            new_image_lookup_field
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
    if "page_num" not in df.columns:
        df['page_num'] = None
    
    df['page_num'].replace('NONE', None, inplace=True)
    df['page_num'].replace('', None, inplace=True)

    df["page_num"] = pd.to_numeric(df["page_num"])

        #     if 'page_num' in deed_pages_df.columns:
            
        # else:
        #     deed_pages_df['page_num'] = None

    if "split_page_num" not in df.columns:
        df['split_page_num'] = None
    df["split_page_num"] = pd.to_numeric(df["split_page_num"])

    if "book_id" not in df.columns:
        df["book_id"] = ''

    if matches_only:
        match_df = df[df['bool_match'] == True].copy()
    else:
        match_df = df

    doc_list_df = df[[
        # 'pk',
        's3_lookup',
        'doc_num',
        'book_id',
        'page_num',
        'split_page_num',
        'page_image_web'
    ]].drop_duplicates()

    print('Join 1')
    # same doc num with multiple pages + splitpage
    doc_num_split_page_df = match_df[(match_df['doc_num'] != '') & (match_df['doc_page_count'] > 1) & (match_df['split_page_num'] >= 1)].copy()

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

    print('Join 2')
    # no doc_num, book and page only, splitpage
    book_id_split_page_df = match_df[(match_df['book_id'] != '') & (match_df['doc_page_count'] == 1) & (match_df['split_page_num'] >= 1)].copy()

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

    print('Join 3')
    # no doc_num, book and page only, no splitpage
    # TODO: Need to incorporate doctype for book and page, maybe create doc_num before this part of pagination, or make book type part of the regex

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

    print('Join 4')
    # no doc_num, book and page only, no splitpage
    doc_num_one_page_df = match_df[(match_df['book_id'] == '') & (match_df['doc_page_count'] == 1)].copy()

    # Don't really need to join, it's just one page
    doc_num_one_page_df['prev_page_image_web'] = ''
    doc_num_one_page_df['next_page_image_web'] = ''
    doc_num_one_page_df['next_next_page_image_web'] = ''
    doc_num_one_page_df['prev_page_image_lookup'] = ''
    doc_num_one_page_df['next_page_image_lookup'] = ''
    doc_num_one_page_df['next_next_page_image_lookup'] = ''

    # print(book_id_no_split_page_df)
    # book_id_no_split_page_df.to_csv('test_join_4.csv')

    print('Join 5')
    # doc_num, no splitpage (everything left over)
    already_matched_lookups = pd.concat([
        doc_num_split_page_df['s3_lookup'],
        book_id_split_page_df['s3_lookup'],
        book_id_no_split_page_df['s3_lookup'],
        doc_num_one_page_df['s3_lookup']
    ])

    print('isolation check')
    doc_num_no_split_page_df = match_df[~match_df['s3_lookup'].isin(already_matched_lookups)].copy()

    print('actual merge')
    print(doc_num_no_split_page_df)
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

    print("Building out_df...")
    out_df = pd.concat([
        doc_num_split_page_df,
        book_id_split_page_df,
        book_id_no_split_page_df,
        doc_num_one_page_df,
        doc_num_no_split_page_df
    ]).copy()

    cols_to_fill = [
        'book_id',
        'doc_num',
        'prev_page_image_web',
        'next_page_image_web',
        'next_next_page_image_web',
        'prev_page_image_lookup',
        'next_page_image_lookup',
        'next_next_page_image_lookup'
    ]
    out_df.loc[:, cols_to_fill] = out_df.loc[:, cols_to_fill].fillna('')
    out_df.reset_index(drop=True, inplace=True)  # Not sure this is necessary or helpful

    out_df = out_df.replace([np.nan], [None])

    return out_df

def tag_prev_next_image_sql(workflow, matches_only=False):

    print('Gathering doc list...')
    full_doc_list_df = pd.DataFrame(DeedPage.objects.filter(
        workflow=workflow
    ).values(
        # 'pk',
        'bool_match',
        'doc_num',
        'book_id',
        'doc_page_count',
        'page_num',
        'split_page_num',
        'page_image_web',
        's3_lookup'
    ))

    match_df = paginate_deedpage_df(full_doc_list_df, matches_only)

    if matches_only:
        objs_to_update = DeedPage.objects.filter(
            workflow=workflow,
            bool_match=True
        ).values('pk', 's3_lookup')
    else:
        objs_to_update = DeedPage.objects.filter(
            workflow=workflow
        ).values('pk', 's3_lookup')

    update_df = pd.DataFrame(objs_to_update).merge(
        match_df[[
            's3_lookup',
            'prev_page_image_web',
            'next_page_image_web',
            'next_next_page_image_web',
            'prev_page_image_lookup',
            'next_page_image_lookup',
            'next_next_page_image_lookup'
        ]].drop_duplicates().fillna(value=''),
        how="left",
        on="s3_lookup"
    )

    print("Updating db objects...")
    # Convert df to DeedPage objs so can be updated...
    dp_objs = [DeedPage(**kv) for kv in update_df.to_dict('records')]
    DeedPage.objects.bulk_update(
        dp_objs,
        [
            'prev_page_image_web',
            'next_page_image_web',
            'next_next_page_image_web',
            'prev_page_image_lookup',
            'next_page_image_lookup',
            'next_next_page_image_lookup'
        ],
        batch_size=5000
    )

# DEPRECATED
def pagination_merge_deedpage(workflow, image_lookup_df, offset=1):
    if offset == -1:
        label = 'prev'
    elif offset == 1:
        label = 'next'
    elif offset == 2:
        label = 'next_next'
    else:
        return False

    exclude_kwargs = {f'{label}_page_image_web__in': ['', None]}

    print(f'Building {label}_dps df...')
    populated_objs = DeedPage.objects.filter(
        workflow=workflow
    ).exclude(
        **exclude_kwargs
    ).values('pk', f'{label}_page_image_web')
    populated_objs = pd.DataFrame(list(populated_objs))

    print(f'{label}_dps merge...')
    populated_objs = populated_objs.merge(
        image_lookup_df.rename(columns={'join_pk': f'{label}_deedpage_id'}),
        how="left",
        left_on=f"{label}_page_image_web",
        right_on="page_image_web"
    ).drop(columns=['page_image_web'])
    return populated_objs
