from django.tasks import task

from apps.parcel.utils.pmtiles_utils import build_pmtiles_export


@task()
def generate_pmtiles_export(workflow_id):
    from apps.zoon.models import ZooniverseWorkflow

    try:
        workflow = ZooniverseWorkflow.objects.get(pk=workflow_id)
    except ZooniverseWorkflow.DoesNotExist:
        return None

    export = build_pmtiles_export(workflow)
    return export.pk
