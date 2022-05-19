from django.shortcuts import render
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.auth.decorators import login_required

from django.db.models import Max
from apps.zoon.models import ZooniverseWorkflow, ZooniverseSubject
from apps.parcel.models import ShpExport, CSVExport, JoinReport

@login_required(login_url='/admin/login/')
def index(request):
    workflows = ZooniverseWorkflow.objects.all()
    context = {
        'workflows': workflows
    }
    return render(request, 'index.html', context)

@login_required(login_url='/admin/login/')
def workflow_summary(request, workflow_id):
    workflow = ZooniverseWorkflow.objects.get(id=workflow_id)
    subjects = ZooniverseSubject.objects.filter(
        workflow=workflow
    )
    last_update = subjects.aggregate(
        last_update=Max('date_updated'))['last_update']

    shp_exports = ShpExport.objects.filter(workflow=workflow).order_by('-created_at')
    csv_exports = CSVExport.objects.filter(workflow=workflow).order_by('-created_at')
    join_reports = JoinReport.objects.filter(workflow=workflow).order_by('-created_at')

    context = {
        'workflow': workflow,
        'shp_exports': shp_exports,
        'csv_exports': csv_exports,
        'join_reports': join_reports,
        'last_update': last_update,
        'subject_count': subjects.count(),
        'covenants_count': subjects.filter(bool_covenant=True).count(),
        'covenants_maybe_count': subjects.filter(bool_covenant=None).count(),
        'mapped_count': subjects.filter(bool_covenant=True, bool_parcel_match=True).count()
    }

    return render(request, 'workflow_summary.html', context)

@login_required(login_url='/admin/login/')
def covenant_matches(request, workflow_id):
    workflow = ZooniverseWorkflow.objects.get(id=workflow_id)
    covenants = ZooniverseSubject.objects.filter(
        workflow=workflow,
        bool_covenant_final=True
    ).annotate(
        matched_parcel_join_strings=ArrayAgg('parcel_matches__parceljoincandidate__join_string')
    ).order_by('addition_final')

    context = {
        'workflow': workflow,
        'covenants': covenants
    }

    return render(request, 'covenant_matches.html', context)
