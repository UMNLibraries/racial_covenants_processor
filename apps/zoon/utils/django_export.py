import os
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
    df.rename(columns={'id': 'db_id'}, inplace=True)
    df.drop(
        columns=['workflow_id', 'zooniverse_subject_id'], inplace=True, errors='ignore')

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