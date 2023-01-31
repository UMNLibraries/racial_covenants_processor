import pandas as pd
from django.db.models import Count

from apps.deed.models import DeedPage

def get_doc_num_page_counts(workflow):
    doc_num_page_counts = DeedPage.objects.filter(workflow=workflow).values('doc_num').annotate(page_count=Count('doc_num')).order_by('-page_count')

    return list(doc_num_page_counts)

def sort_doc_nums_by_page_count(doc_num_page_counts):
    df = pd.DataFrame(doc_num_page_counts)

    # df = pd.DataFrame([
    #     {'doc_num': '1', 'page_count': 25},
    #     {'doc_num': '2', 'page_count': 2},
    #     {'doc_num': '3', 'page_count': 5},
    #     {'doc_num': '4', 'page_count': 5},
    #     {'doc_num': '5', 'page_count': 25},
    #     {'doc_num': '6', 'page_count': 1},
    #     {'doc_num': '7', 'page_count': 1},
    #     {'doc_num': '8', 'page_count': 2},
    #     {'doc_num': '9', 'page_count': 2},
    #     {'doc_num': '10', 'page_count': 25},
    # ])

    # df['docs_with_count'] = df.groupby(['page_count'])['doc_num'].transform(lambda x: ','.join(x))
    out_df = df.groupby(['page_count'])['doc_num'].apply(list).reset_index(name='docs_with_count_list')
    count_records = out_df[['page_count', 'docs_with_count_list']].to_dict('records')
    return count_records

def make_chunks(full_list, chunk_size):
    # chunk_size = 4
    chunks = []
    for i in range(0, len(full_list), chunk_size):
        chunk = full_list[i:i+chunk_size]
        chunks.append(chunk)
    return chunks

def update_docs_with_page_counts(workflow, count_records, batch_size=10000):
    # This should be moved to the gather_deed_images management command as part of the pandas stage BEFORE insertion into the database.

    for page_count in count_records:
        # if page_count['page_count'] == 1:
        #     print('Page count: 1. Ignoring now and will update by default later')
        # else:
        print(f"Page count: {page_count['page_count']}")
        # Divide into batches of n doc_nums at a time divided by number of pages
        batches = make_chunks(page_count['docs_with_count_list'], int(batch_size / page_count['page_count']))
        for b in batches:
            DeedPage.objects.filter(
                workflow=workflow,
                doc_page_count=None,  # TEMP TEMP TEMP
                doc_num__in=b
            ).update(doc_page_count=page_count['page_count'])
            print(f'    Updated {len(b)} doc_nums...')

    # print("Assuming page counts that are still None are 1-pagers. Setting doc_page_count to 1...")
    # DeedPage.objects.filter(workflow=workflow, doc_page_count=None).update(doc_page_count=1)
