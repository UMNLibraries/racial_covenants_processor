import os
import json
import datetime
import pandas as pd

from django.db.models import F
from django.utils.text import slugify
from django.apps import apps

from apps.zoon.models import ZooniverseResponseProcessed

from django.conf import settings


def save_backup_file(df, workflow_name, filename_root):
    backup_dir = os.path.join(settings.BASE_DIR, 'data', 'backup')
    os.makedirs(backup_dir, exist_ok=True)

    outfile = os.path.join(backup_dir,
                            f'{filename_root}_{slugify(workflow_name)}_{datetime.datetime.now().date()}.csv')
    print(outfile)
    df.to_csv(outfile, index=False)

    return outfile


def dump_cx_model_backups(workflow, app_name, model_name):
    workflow_name = workflow.workflow_name
    model = apps.get_model(app_name, model_name)

    objs = model.objects.filter(
        workflow__workflow_name=workflow_name
    ).annotate(
        workflow_name=F('workflow__workflow_name')
    ).values()

    df = pd.DataFrame(objs)
    if df.shape[0] == 0:
        print (f"No {model_name} records found in workflow {workflow_name}")
        return False
    df.rename(columns={'id': 'db_id'}, inplace=True)
    df.drop(
        columns=['workflow_id', 'zooniverse_subject_id'], inplace=True, errors='ignore')
    
    print(df.columns)
    if model_name == 'ZooniverseSubject':
        df['image_ids'] = df['image_ids'].apply(lambda x: json.dumps(x))
        df['image_links'] = df['image_links'].apply(lambda x: json.dumps(x))
        df['join_candidates'] = df['join_candidates'].apply(lambda x: json.dumps(x))
        df['parcel_addresses'] = df['parcel_addresses'].apply(lambda x: json.dumps(x))

    print(df)
    outfile = save_backup_file(df, workflow_name, model_name.lower())

    return outfile


def dump_individual_response_model_backups(workflow):
    workflow_name = workflow.workflow_name

    objs = ZooniverseResponseProcessed.objects.filter(
        workflow__workflow_name=workflow_name
    ).annotate(
        workflow_name=F('workflow__workflow_name'),
        zoon_subject_id=F('subject__zoon_subject_id'),
        zoon_workflow_id=F('workflow__zoon_id')
    ).values()

    df = pd.DataFrame(objs)
    df.rename(columns={'id': 'db_id'}, inplace=True)
    df.drop(
        columns=['workflow_id', 'subject_id', 'response_raw_id'], inplace=True, errors='ignore')

    print(df)
    outfile = save_backup_file(df, workflow_name, 'zooniverseresponseprocessed')

    return outfile


def check_workflow_match(workflow, infile_path):
    '''This function checks to see if the workflow in the CSV matches the specified workflow from the user command'''
    
    df = pd.read_csv(infile_path)
    workflow_names = df.workflow_name.drop_duplicates().to_list()
    if len(workflow_names) > 1:
        print("Hmm, there is more than 1 workflow name in this import file. Exiting.")
        return False
    
    if workflow.workflow_name == workflow_names[0]:
        print("Workflow name in CSV matches selected workflow.")
        return True
    else:
        print("Workflow name in CSV DOES NOT match selected workflow. Exiting. (NOTE: If you would like to migrate subjects to a new workflow, you can manually replace values in this CSV with values from the new workflow and try importing again.)")
        return False