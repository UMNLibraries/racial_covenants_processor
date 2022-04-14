from django.shortcuts import render

from django.db.models import Max
from apps.zoon.models import ZooniverseWorkflow, ZooniverseSubject


def workflow_summary(request, workflow_id):
    workflow = ZooniverseWorkflow.objects.get(id=workflow_id)
    subjects = ZooniverseSubject.objects.filter(
        workflow=workflow
    )
    last_update = subjects.aggregate(
        last_update=Max('date_updated'))['last_update']

    context = {
        'workflow': workflow,
        'last_update': last_update,
        'subject_count': subjects.count(),
        'covenants_count': subjects.filter(bool_covenant=True).count(),
        'covenants_maybe_count': subjects.filter(bool_covenant=None).count(),
        'mapped_count': subjects.filter(bool_covenant=True, bool_parcel_match=True).count()
    }

    return render(request, 'workflow_summary.html', context)
