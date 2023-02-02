import pandas as pd
from django.db.models import Count, OuterRef, Subquery, F, Q, Case, When, Value, ImageField

from apps.deed.models import DeedPage

def tag_doc_num_page_counts(df):
    page_counts = df[['doc_num', 'public_uuid']].groupby(['doc_num']).count().reset_index().rename(columns={'public_uuid': 'doc_page_count'})
    # page_counts = df[['doc_num']].value_counts().reset_index(names='doc_page_count')
    print(page_counts)
    return df.merge(
        page_counts,
        how='left',
        on='doc_num'
    )

# def find_prev_next_image(doc_list, doc_num, book_id, doc_page_count, page_num, split_page_num, offset=1):
#     '''Warning: offsets other than -1, 1 and 2 are untested'''
#     '''In pandas land this should probably be written as a series of merges for different conditions'''
#     match_generator = None
#     # same doc num with multiple pages + splitpage
#     if split_page_num:
#         if doc_page_count > 1 and split_page_num >= 1:
#             match_generator = (
#                 page for page in doc_list if page['doc_num'] == doc_num and page['split_page_num'] == (split_page_num + offset)
#             )
#         # no doc_num, book and page only, splitpage
#         elif doc_page_count == 1 and split_page_num >= 1:
#             match_generator = (
#                 page for page in doc_list if page['book_id'] == book_id and page['split_page_num'] == (split_page_num + offset)
#             )
#     elif page_num:
#         # no doc_num, book and page only, no splitpage
#         if doc_page_count == 1:
#             match_generator = (
#                 page for page in doc_list if page['book_id'] == book_id and page['page_num'] == (page_num + offset)
#             )
#         else:
#             match_generator = (
#                 page for page in doc_list if page['doc_num'] == doc_num and page['page_num'] == (page_num + offset)
#             )
#
#     if match_generator:
#         result = next(match_generator, None)
#         if result:
#             return result['page_image_web']
#     return None

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

    match_df = match_df.merge(
        doc_list_df[[
            doc_or_book_selector,
            f'{split_str}page_num',
            'page_image_web'
        ]].rename(columns={
            'page_image_web': new_image_field,
            f'{split_str}page_num': f'{split_str}page_num_right'
        }),
        how="left",
        left_on=[doc_or_book_selector, f"{split_str}page_num_{offset}"],
        right_on=[doc_or_book_selector, f"{split_str}page_num_right"]
    ).drop(columns=[f"{split_str}page_num_right"])

    return match_df

def tag_prev_next_image_sql(workflow):

    # hit_object_pks = DeedPage.objects.filter(
    #     workflow=workflow,
    #     bool_match=True
    # ).values_list('pk', flat=True)
    print('Gathering doc list...')
    doc_list_df = pd.DataFrame(DeedPage.objects.filter(
        workflow=workflow
    ).values(
        'doc_num',
        'book_id',
        # 'doc_page_count',
        'page_num',
        'split_page_num',
        'page_image_web',
        's3_lookup'
    ))

    # doc_num_list_df = doc_list_df[~doc_list_df['doc_num'].isna()].drop(columns=['book_id'])
    # book_id_list_df = doc_list_df[doc_list_df['s3_lookup'].isin(doc_num_list_df['s3_lookup'])].drop(columns=['doc_num'])
    #
    # # S3 lookup shouldn't be needed anymore on these two
    # doc_num_list_df.drop(columns=['s3_lookup', 'doc_page_count'], inplace=True)
    # book_id_list_df.drop(columns=['s3_lookup', 'doc_page_count'], inplace=True)

    # update_objs = []
    # counter = 0

    print('Prepping DeedPage matches for update...')
    match_df = pd.DataFrame(DeedPage.objects.filter(
        workflow=workflow,
        bool_match=True
    ).values(
        's3_lookup',
        'doc_num',
        'book_id',
        'doc_page_count',
        'page_num',
        'split_page_num'
    ))

    print('Join 1')
    # same doc num with multiple pages + splitpage
    doc_num_split_page_df = match_df[(match_df['doc_page_count'] > 1) & (match_df['split_page_num'] >= 1)]

    for offset in [-1, 1, 2]:
        doc_num_split_page_df = pagination_merge(
            doc_num_split_page_df,
            doc_list_df,
            'doc_num',
            offset=offset,
            split_page=True
        )

    # doc_num_split_page_df['split_page_minus_1'] = doc_num_split_page_df['split_page_num'] - 1
    # doc_num_split_page_df['split_page_plus_1'] = doc_num_split_page_df['split_page_num'] + 1
    # doc_num_split_page_df['split_page_plus_2'] = doc_num_split_page_df['split_page_num'] + 2
    #
    # # prev page
    # doc_num_split_page_df = doc_num_split_page_df.merge(
    #     doc_list_df[[
    #         'doc_num',
    #         'split_page_num',
    #         'page_image_web'
    #     ]].rename(columns={
    #         'page_image_web': 'prev_page_image_web',
    #         'split_page_num': 'split_page_num_right'
    #     }),
    #     how="left",
    #     left_on=["doc_num", "split_page_minus_1"],
    #     right_on=["doc_num", "split_page_num_right"]
    # ).drop(columns=["split_page_num_right"])
    #
    # # next page
    # doc_num_split_page_df = doc_num_split_page_df.merge(
    #     doc_list_df[[
    #         'doc_num',
    #         'split_page_num',
    #         'page_image_web'
    #     ]].rename(columns={
    #         'page_image_web': 'next_page_image_web',
    #         'split_page_num': 'split_page_num_right'
    #     }),
    #     how="left",
    #     left_on=["doc_num", "split_page_plus_1"],
    #     right_on=["doc_num", "split_page_num_right"]
    # ).drop(columns=["split_page_num_right"])
    #
    # # next next page
    # doc_num_split_page_df = doc_num_split_page_df.merge(
    #     doc_list_df[[
    #         'doc_num',
    #         'split_page_num',
    #         'page_image_web'
    #     ]].rename(columns={
    #         'page_image_web': 'next_next_page_image_web',
    #         'split_page_num': 'split_page_num_right'
    #     }),
    #     how="left",
    #     left_on=["doc_num", "split_page_plus_2"],
    #     right_on=["doc_num", "split_page_num_right"]
    # ).drop(columns=["split_page_num_right"])

    print(doc_num_split_page_df)
    doc_num_split_page_df.to_csv('test_join_1.csv')

    print('Join 2')
    # no doc_num, book and page only, splitpage
    book_id_split_page_df = match_df[(match_df['doc_page_count'] == 1) & (match_df['split_page_num'] >= 1)]

    for offset in [-1, 1, 2]:
        book_id_split_page_df = pagination_merge(
            book_id_split_page_df,
            doc_list_df,
            'book_id',
            offset=offset,
            split_page=True
        )

    # book_id_split_page_df['split_page_plus_1'] = book_id_split_page_df['split_page_num'] + 1
    # book_id_split_page_df = book_id_split_page_df.merge(
    #     doc_list_df[[
    #         'book_id',
    #         'split_page_num',
    #         'page_image_web'
    #     ]].rename(columns={
    #         'page_image_web': 'next_page_image_web',
    #         'split_page_num': 'split_page_num_right'
    #     }),
    #     how="left",
    #     left_on=["book_id", "split_page_plus_1"],
    #     right_on=["book_id", "split_page_num_right"]
    # ).drop(columns=["split_page_num_right"])
    #
    print(book_id_split_page_df)
    book_id_split_page_df.to_csv('test_join_2.csv')

    print('Join 3')
    # no doc_num, book and page only, no splitpage
    book_id_no_split_page_df = match_df[match_df['doc_page_count'] == 1]

    for offset in [-1, 1, 2]:
        book_id_no_split_page_df = pagination_merge(
            book_id_no_split_page_df,
            doc_list_df,
            'book_id',
            offset=offset,
            split_page=False
        )

    # book_id_no_split_page_df['page_num_plus_1'] = book_id_no_split_page_df['page_num'] + 1
    # book_id_no_split_page_df = book_id_no_split_page_df.merge(
    #     doc_list_df[[
    #         'book_id',
    #         'page_num',
    #         'page_image_web'
    #     ]].rename(columns={
    #         'page_image_web': 'next_page_image_web',
    #         'page_num': 'page_num_right'
    #     }),
    #     how="left",
    #     left_on=["book_id", "page_num_plus_1"],
    #     right_on=["book_id", "page_num_right"]
    # ).drop(columns=["page_num_right"])

    print(book_id_no_split_page_df)
    book_id_no_split_page_df.to_csv('test_join_3.csv')

    print('Join 4')
    # doc_num, no splitpage (everything left over)
    already_matched_lookups = pd.concat([
        doc_num_split_page_df['s3_lookup'],
        book_id_split_page_df['s3_lookup'],
        book_id_no_split_page_df['s3_lookup']
    ])
    print(already_matched_lookups.shape)
    print(match_df.shape)

    match_df.to_csv('match_df.csv')

    doc_num_no_split_page_df = match_df[~match_df['s3_lookup'].isin(already_matched_lookups)]

    for offset in [-1, 1, 2]:
        doc_num_no_split_page_df = pagination_merge(
            doc_num_no_split_page_df,
            doc_list_df,
            'doc_num',
            offset=offset,
            split_page=False
        )

    # doc_num_no_split_page_df['page_num_plus_1'] = doc_num_no_split_page_df['page_num'] + 1
    #
    # doc_num_no_split_page_df = doc_num_no_split_page_df.merge(
    #     doc_list_df[[
    #         'doc_num',
    #         'page_num',
    #         'page_image_web'
    #     ]].rename(columns={
    #         'page_image_web': 'next_page_image_web',
    #         'page_num': 'page_num_right'
    #     }),
    #     how="left",
    #     left_on=["doc_num", "page_num_plus_1"],
    #     right_on=["doc_num", "page_num_right"]
    # ).drop(columns=['page_num_right'])

    print(doc_num_no_split_page_df)
    doc_num_no_split_page_df.to_csv('test_join_4.csv')

    # # doc_page_count_x, page_num_x, split_page_num_x, page_plus_1, pk, doc_num, doc_page_count_y, page_num_y, split_page_num_y
    #


# elif page_num:
#     # no doc_num, book and page only, no splitpage
#     if doc_page_count == 1:
#         match_generator = (
#             page for page in doc_list if page['book_id'] == book_id and page['page_num'] == (page_num + offset)
#         )
#     else:
#         match_generator = (
#             page for page in doc_list if page['doc_num'] == doc_num and page['page_num'] == (page_num + offset)
#         )


    # for d in DeedPage.objects.filter(
    #     workflow=workflow,
    #     bool_match=True
    # ).only(
    #     's3_lookup',
    #     'doc_num',
    #     'book_id',
    #     'doc_page_count',
    #     'page_num',
    #     'split_page_num'
    # ):
    #     if d.doc_num:
    #         doc_small_list = [doc for doc in doc_list if doc['doc_num'] == d.doc_num]
    #     elif d.book_id:
    #         doc_small_list = [doc for doc in doc_list if doc['book_id'] == d.book_id]
    #
    #     # TODO: Maybe first isolate by doc_num or book_num to reduce searching over whole set...
    #     d.prev_page_image_web=find_prev_next_image(
    #         doc_small_list,
    #         d.doc_num,
    #         d.book_id,
    #         d.doc_page_count,
    #         d.page_num,
    #         d.split_page_num,
    #         offset=-1
    #     )
    #     d.next_page_image_web=find_prev_next_image(
    #         doc_small_list,
    #         d.doc_num,
    #         d.book_id,
    #         d.doc_page_count,
    #         d.page_num,
    #         d.split_page_num,
    #         offset=1
    #     )
    #     d.next_next_page_image_web=find_prev_next_image(
    #         doc_small_list,
    #         d.doc_num,
    #         d.book_id,
    #         d.doc_page_count,
    #         d.page_num,
    #         d.split_page_num,
    #         offset=2
    #     )
    #     update_objs.append(d)
    #     counter += 1
    #     if counter % 1000 == 0:
    #         print(f'{counter} records...')
    #         print('Running update queries...')
    #         DeedPage.objects.bulk_update(update_objs, ['prev_page_image_web', 'next_page_image_web', 'next_next_page_image_web'], batch_size=100)
    #         update_objs = []
    #         print('Update complete.')
    #
    # # TODO: Connection is likely to be lost by this time, so need to do new connection when it's time for updates.
    # print('Running remaining update queries...')
    # DeedPage.objects.bulk_update(update_objs, ['prev_page_image_web', 'next_page_image_web', 'next_next_page_image_web'], batch_size=100)

    # pk_chunks = make_chunks(hit_object_pks, 100)
    #
    # for chunk in pk_chunks[0:1]:
    #     print(chunk)
    #
    #     hit_objects = DeedPage.objects.filter(
    #         pk__in=chunk
    #     ).annotate(
    #         prev_page_image_web_temp=Case(
    #             When(
    #                 bool_match=False, then=Value('')
    #             ),
    #             # same doc num with multiple pages + splitpage
    #             When(
    #                 Q(doc_page_count__gt=1) & Q(split_page_num__gte=1), then=Subquery(
    #                     DeedPage.objects.filter(workflow=OuterRef('workflow'), doc_num=OuterRef('doc_num'), split_page_num=OuterRef('split_page_num') - 1).order_by('-pk').values('page_image_web')[:1]
    #                 )
    #             ),
    #             # no doc_num, book and page only, splitpage
    #             When(
    #                 Q(doc_page_count=1) & Q(split_page_num__gte=1), then=Subquery(
    #                     DeedPage.objects.filter(workflow=OuterRef('workflow'), book_id=OuterRef('book_id'), split_page_num=OuterRef('split_page_num') - 1).order_by('-pk').values('page_image_web')[:1]
    #                 )
    #             ),
    #             # no doc_num, book and page only, no splitpage
    #             When(
    #                 Q(doc_page_count=1), then=Subquery(
    #                     DeedPage.objects.filter(workflow=OuterRef('workflow'), book_id=OuterRef('book_id'), page_num=OuterRef('page_num') - 1).order_by('-pk').values('page_image_web')[:1]
    #                 )
    #             ),
    #             default=Subquery(
    #                 # same doc num with multiple pages
    #                 DeedPage.objects.filter(workflow=OuterRef('workflow'), doc_num=OuterRef('doc_num'), page_num=OuterRef('page_num') - 1).order_by('-pk').values('page_image_web')[:1]
    #             ),
    #             output_field=ImageField()
    #         # ),
    #         # next_page_image_web_temp=Case(
    #         #     When(
    #         #         bool_match=False, then=Value('')
    #         #     ),
    #         #     # same doc num with multiple pages + splitpage
    #         #     When(
    #         #         Q(doc_page_count__gt=1) & Q(split_page_num__gte=1), then=Subquery(
    #         #             DeedPage.objects.filter(workflow=OuterRef('workflow'), doc_num=OuterRef('doc_num'), split_page_num=OuterRef('split_page_num') + 1).order_by('-pk').values('page_image_web')[:1]
    #         #         )
    #         #     ),
    #         #     # no doc_num, book and page only, splitpage
    #         #     When(
    #         #         Q(doc_page_count=1) & Q(split_page_num__gte=1), then=Subquery(
    #         #             DeedPage.objects.filter(workflow=OuterRef('workflow'), book_id=OuterRef('book_id'), split_page_num=OuterRef('split_page_num') + 1).order_by('-pk').values('page_image_web')[:1]
    #         #         )
    #         #     ),
    #         #     # no doc_num, book and page only, no splitpage
    #         #     When(
    #         #         Q(doc_page_count=1), then=Subquery(
    #         #             DeedPage.objects.filter(workflow=OuterRef('workflow'), book_id=OuterRef('book_id'), page_num=OuterRef('page_num') + 1).order_by('-pk').values('page_image_web')[:1]
    #         #         )
    #         #     ),
    #         #     default=Subquery(
    #         #         # same doc num with multiple pages
    #         #         DeedPage.objects.filter(workflow=OuterRef('workflow'), doc_num=OuterRef('doc_num'), page_num=OuterRef('page_num') + 1).order_by('-pk').values('page_image_web')[:1]
    #         #     ),
    #         #     output_field=ImageField()
    #         # ),
    #         # next_next_page_image_web_temp=Case(
    #         #     When(
    #         #         bool_match=False, then=Value('')
    #         #     ),
    #         #     # same doc num with multiple pages + splitpage
    #         #     When(
    #         #         Q(doc_page_count__gt=1) & Q(split_page_num__gte=1), then=Subquery(
    #         #             DeedPage.objects.filter(workflow=OuterRef('workflow'), doc_num=OuterRef('doc_num'), split_page_num=OuterRef('split_page_num') + 2).order_by('-pk').values('page_image_web')[:1]
    #         #         )
    #         #     ),
    #         #     # no doc_num, book and page only, splitpage
    #         #     When(
    #         #         Q(doc_page_count=1) & Q(split_page_num__gte=1), then=Subquery(
    #         #             DeedPage.objects.filter(workflow=OuterRef('workflow'), book_id=OuterRef('book_id'), split_page_num=OuterRef('split_page_num') + 2).order_by('-pk').values('page_image_web')[:1]
    #         #         )
    #         #     ),
    #         #     # no doc_num, book and page only, no splitpage
    #         #     When(
    #         #         Q(doc_page_count=1), then=Subquery(
    #         #             DeedPage.objects.filter(workflow=OuterRef('workflow'), book_id=OuterRef('book_id'), page_num=OuterRef('page_num') + 2).order_by('-pk').values('page_image_web')[:1]
    #         #         )
    #         #     ),
    #         #     default=Subquery(
    #         #         # same doc num with multiple pages
    #         #         DeedPage.objects.filter(workflow=OuterRef('workflow'), doc_num=OuterRef('doc_num'), page_num=OuterRef('page_num') + 2).order_by('-pk').values('page_image_web')[:1]
    #         #     ),
    #         #     output_field=ImageField()
    #         )
    #     )
    #     with (open('query_test.txt', 'w') as testfile):
    #         testfile.write(str(hit_objects.query))
    #
    #
    #     hit_objects.update(
    #         prev_page_image_web=F('prev_page_image_web_temp')
    #         # next_page_image_web=F('next_page_image_web_temp'),
    #         # next_next_page_image_web=F('next_next_page_image_web_temp')
    #     )



# Methods here and lower are mostly deprecated, but can be used to update page counts on deedpage records that need to be updated (rather than re-imported, which is faster and preferable)
# def get_doc_num_page_counts(workflow):
#     doc_num_page_counts = DeedPage.objects.filter(workflow=workflow).values('doc_num').annotate(page_count=Count('doc_num')).order_by('-page_count')
#
#     return list(doc_num_page_counts)
#
# def sort_doc_nums_by_page_count(doc_num_page_counts):
#     df = pd.DataFrame(doc_num_page_counts)
#
#     out_df = df.groupby(['page_count'])['doc_num'].apply(list).reset_index(name='docs_with_count_list')
#     count_records = out_df[['page_count', 'docs_with_count_list']].to_dict('records')
#     return count_records
#
# def make_chunks(full_list, chunk_size):
#     # chunk_size = 4
#     chunks = []
#     for i in range(0, len(full_list), chunk_size):
#         chunk = full_list[i:i+chunk_size]
#         chunks.append(chunk)
#     return chunks
#
# def update_docs_with_page_counts(workflow, count_records, batch_size=10000):
#     # This should be moved to the gather_deed_images management command as part of the pandas stage BEFORE insertion into the database.
#
#     for page_count in count_records:
#         # if page_count['page_count'] == 1:
#         #     print('Page count: 1. Ignoring now and will update by default later')
#         # else:
#         print(f"Page count: {page_count['page_count']}")
#         # Divide into batches of n doc_nums at a time divided by number of pages
#         batches = make_chunks(page_count['docs_with_count_list'], int(batch_size / page_count['page_count']))
#         for b in batches:
#             DeedPage.objects.filter(
#                 workflow=workflow,
#                 doc_page_count=None,  # TEMP TEMP TEMP
#                 doc_num__in=b
#             ).update(doc_page_count=page_count['page_count'])
#             print(f'    Updated {len(b)} doc_nums...')
#
#     # print("Assuming page counts that are still None are 1-pagers. Setting doc_page_count to 1...")
#     # DeedPage.objects.filter(workflow=workflow, doc_page_count=None).update(doc_page_count=1)
