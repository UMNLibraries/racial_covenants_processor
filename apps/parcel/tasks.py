import logging

from django.conf import settings
from django.tasks import task

from apps.parcel.utils.pmtiles_utils import build_pmtiles_export

logger = logging.getLogger(__name__)


@task()
def generate_pmtiles_export(workflow_id):
    if settings.DEBUG:
        logger.info(
            "DEBUG mode: skipping PMTiles export for workflow_id=%s",
            workflow_id,
        )
        return None

    from apps.zoon.models import ZooniverseWorkflow

    try:
        workflow = ZooniverseWorkflow.objects.get(pk=workflow_id)
    except ZooniverseWorkflow.DoesNotExist:
        return None

    export = build_pmtiles_export(workflow)
    return export.pk
