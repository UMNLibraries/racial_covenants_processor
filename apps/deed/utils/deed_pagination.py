import numpy as np
import pandas as pd
from django.db.models import Count, OuterRef, Subquery, F, Q, Case, When, Value, ImageField
from django.db import connection

from apps.deed.models import DeedPage


def tag_doc_num_page_counts(df):
    if 'batch_id' in df.columns:
        setup_fields = ['batch_id', 'doc_num', 'public_uuid']
        groupby_fields = ['batch_id', 'doc_num']
    else:
        setup_fields = ['doc_num', 'public_uuid']
        groupby_fields = ['doc_num']
    page_counts = df[setup_fields].groupby(groupby_fields).count().reset_index().rename(columns={'public_uuid': 'doc_page_count'})
    # page_counts = df[['doc_num']].value_counts().reset_index(names='doc_page_count')
    # print(page_counts)
    return df.merge(
        page_counts,
        how='left',
        on=groupby_fields
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
            'doc_type',
            'batch_id',
            doc_or_book_selector,
            f'{split_str}page_num_right',
            new_image_field,
            new_image_lookup_field
        ]],
        how="left",
        left_on=["doc_type", "batch_id", doc_or_book_selector, f"{split_str}page_num_{offset}"],
        right_on=["doc_type", "batch_id", doc_or_book_selector, f"{split_str}page_num_right"]
    ).drop(columns=[f"{split_str}page_num_right"]).drop_duplicates(subset=['s3_lookup'])

    return match_df

def round_float_to_str(x):
    try:
        return str(round(x))
    except:
        return 'None'

def paginate_deedpage_df(df, matches_only=False):

    # TODO: Change page_num and split_page_num to ints
    if "page_num" not in df.columns:
        df['page_num'] = None
    
    df['page_num'].replace('NONE', None, inplace=True)
    df['page_num'].replace('', None, inplace=True)

    df["page_num"] = pd.to_numeric(df["page_num"])

    if "split_page_num" not in df.columns:
        df['split_page_num'] = None
    df["split_page_num"] = pd.to_numeric(df["split_page_num"])

    if "doc_type" not in df.columns:
        df["doc_type"] = ''

    if 'batch_id' in df.columns:
        df['batch_id'].fillna('', inplace=True)
    else:
        df['batch_id'] = ''

    if 'doc_alt_id' in df.columns:
        df['doc_alt_id'].fillna('', inplace=True)
    else:
        df['doc_alt_id'] = ''

    # If doc_num is null, use doc_type/book/page as doc_num
    if "doc_num" not in df.columns:
        df["doc_num"] = ''
    df['doc_num'] = df['doc_num'].str.replace('NONE', '')
    df['doc_num'] = df['doc_num'].fillna('')
    if 'book_id' in df.columns:
        df['book_id'] = df['book_id'].str.replace('NONE', '')
        df['book_id'] = df['book_id'].fillna('')

        df.loc[(df['doc_num'] == '') & (df['book_id'] != ''), 'doc_num'] = df['doc_type'] + ' Book ' + df['book_id'] + ' Page ' + df['page_num'].apply(lambda x: round_float_to_str(x))

    if "book_id" not in df.columns:
        df["book_id"] = ''

    # Drop duplicates for non-unique doc_num, book_id, page_num, split_page combos
    print("Dropping duplicate doc/page/split page combos...")
    df = df.drop_duplicates(subset=['doc_type', 'batch_id', 'doc_num', 'book_id', 'page_num', 'split_page_num'])

    # Tag docs with page count by doc_num
    print('Tagging doc num page counts...')
    df = tag_doc_num_page_counts(df)

    if matches_only:
        match_df = df[df['bool_match'] == True].copy()
    else:
        match_df = df

    print(f'Starting with {match_df.shape[0]} objects...')

    doc_list_df = df[[
        # 'pk',
        's3_lookup',
        'doc_type',
        'batch_id',
        'doc_num',
        'book_id',
        'page_num',
        'split_page_num',
        'page_image_web'
    ]].drop_duplicates()

    print('Join 1')
    # same doc num with multiple pages + splitpage
    doc_num_split_page_df = match_df[(match_df['doc_num'] != '') & (match_df['doc_page_count'] > 1) & (match_df['split_page_num'] >= 1)].copy()

    print(f'Join 1 input: {doc_num_split_page_df.shape[0]} objects')
    for offset in [-1, 1, 2]:
        doc_num_split_page_df = pagination_merge(
            doc_num_split_page_df,
            doc_list_df,
            'doc_num',
            offset=offset,
            split_page=True
        )

    validation_fields = ['s3_lookup', 'doc_type', 'doc_num', 'book_id', 'page_num', 'split_page_num', 'doc_page_count']
    page_to_find = None
    # page_to_find = 'OlmstedCountyAbstracts/OldDeedBooks/D-102/HDEED102192'

    print(doc_num_split_page_df[validation_fields])
    if page_to_find:
        print('Searching for target page...')
        print(doc_num_split_page_df[doc_num_split_page_df['s3_lookup'] == page_to_find][validation_fields])
    # print(f'Join 1 output: {doc_num_split_page_df.shape[0]} objects')
    # doc_num_split_page_df.to_csv('test_join_1.csv')

    print('Join 2')
    # no doc_num, book and page only, splitpage
    book_id_split_page_df = match_df[(match_df['book_id'] != '') & (match_df['doc_page_count'] == 1) & (match_df['split_page_num'] >= 1)].copy()
    print(f'Join 2 input: {book_id_split_page_df.shape[0]} objects')

    for offset in [-1, 1, 2]:
        book_id_split_page_df = pagination_merge(
            book_id_split_page_df,
            doc_list_df,
            'book_id',
            offset=offset,
            split_page=True
        )

    print(book_id_split_page_df[validation_fields])
    if page_to_find:
        print('Searching for target page...')
        print(book_id_split_page_df[book_id_split_page_df['s3_lookup'] == page_to_find][validation_fields])

    # print(f'Join 2 output: {book_id_split_page_df.shape[0]} objects')
    # book_id_split_page_df.to_csv('test_join_2.csv')

    print('Join 3')
    # no doc_num, book and page only, no splitpage
    # TODO: Need to incorporate doctype for book and page, maybe create doc_num before this part of pagination, or make book type part of the regex

    book_id_no_split_page_df = match_df[(match_df['book_id'] != '') & (~match_df['page_num'].isna()) & (match_df['doc_page_count'] == 1)].copy()
    print(f'Join 3 input: {book_id_no_split_page_df.shape[0]} objects')

    for offset in [-1, 1, 2]:
        book_id_no_split_page_df = pagination_merge(
            book_id_no_split_page_df,
            doc_list_df,
            'book_id',
            offset=offset,
            split_page=False
        )

    print(book_id_no_split_page_df[validation_fields])
    if page_to_find:
        print('Searching for target page...')
        print(book_id_no_split_page_df[book_id_no_split_page_df['s3_lookup'] == page_to_find][validation_fields])
    # print(f'Join 3 output: {book_id_no_split_page_df.shape[0]} objects')
    # book_id_no_split_page_df.to_csv('test_join_3.csv')

    print('Join 4')
    # No splitpage, one page
    # Old explanation: no doc_num, book and page only, no splitpage <-- this doesn't make sense
    doc_num_one_page_df = match_df[(match_df['page_num'].isna()) & (match_df['doc_page_count'] == 1)].copy()
    # doc_num_one_page_df = match_df[(match_df['book_id'] == '') & (match_df['doc_page_count'] == 1)].copy()

    
    print(f'Join 4 input: {doc_num_one_page_df.shape[0]} objects')

    # Don't really need to join, it's just one page
    doc_num_one_page_df['prev_page_image_web'] = ''
    doc_num_one_page_df['next_page_image_web'] = ''
    doc_num_one_page_df['next_next_page_image_web'] = ''
    doc_num_one_page_df['prev_page_image_lookup'] = ''
    doc_num_one_page_df['next_page_image_lookup'] = ''
    doc_num_one_page_df['next_next_page_image_lookup'] = ''

    print(doc_num_one_page_df[validation_fields])
    if page_to_find:
        print('Searching for target page...')
        print(doc_num_one_page_df[doc_num_one_page_df['s3_lookup'] == page_to_find][validation_fields])
    # print(f'Join 4 output: {doc_num_one_page_df.shape[0]} objects')
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
    print(f'Join 5 input: {doc_num_no_split_page_df.shape[0]} objects')

    # print('actual merge')
    # print(doc_num_no_split_page_df.shape)
    # print(doc_num_no_split_page_df[['s3_lookup', 'doc_num', 'book_id', 'page_num', 'split_page_num', 'doc_page_count']])

    # print('dropping duplicates...')
    # doc_num_no_split_page_df = doc_num_no_split_page_df.drop_duplicates()
    # print(doc_num_no_split_page_df.shape)
    # print(doc_num_no_split_page_df[['s3_lookup', 'doc_num', 'book_id', 'page_num', 'split_page_num', 'doc_page_count']])

    for offset in [-1, 1, 2]:
        doc_num_no_split_page_df = pagination_merge(
            doc_num_no_split_page_df,
            doc_list_df,
            'doc_num',
            offset=offset,
            split_page=False
        )

    print(doc_num_no_split_page_df[validation_fields])
    if page_to_find:
        print('Searching for target page...')
        print(doc_num_no_split_page_df[doc_num_no_split_page_df['s3_lookup'] == page_to_find][validation_fields])
    # print(f'Join 5 output: {doc_num_no_split_page_df.shape[0]} objects')
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
    out_df["page_num"] = out_df["page_num"].astype(pd.Int64Dtype())
    out_df["split_page_num"] = out_df["split_page_num"].astype(pd.Int64Dtype())

    out_df = out_df.drop(columns=[
        'page_num_-1',
        'page_num_1',
        'page_num_2',
        'split_page_num_-1',
        'split_page_num_1',
        'split_page_num_2',
    ])

    print(out_df[validation_fields])

    return out_df

def tag_prev_next_image_sql(workflow, matches_only=False):

    print('Gathering doc list...')
    full_doc_list_df = pd.DataFrame(DeedPage.objects.filter(
        workflow=workflow
    ).values(
        # 'pk',
        'bool_match',
        'doc_type',
        'doc_num',
        'public_uuid',
        'batch_id',
        'book_id',
        # 'doc_page_count',  # Generating duplicate at next stage. Could also drop in next stage before merging.
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
            'doc_page_count',
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
            'doc_page_count',
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
