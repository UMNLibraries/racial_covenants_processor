from django.shortcuts import render
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.auth.decorators import login_required

from django.db.models import Max
from apps.deed.models import SearchHitReport
from apps.zoon.models import ZooniverseWorkflow, ZooniverseSubject
from apps.parcel.models import GeoJSONExport, ShpExport, CSVExport, JoinReport, Parcel

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

    mapped_count = Parcel.covenant_objects.filter(workflow=workflow).count()

    geojson_exports = GeoJSONExport.objects.filter(workflow=workflow).order_by('-created_at')
    shp_exports = ShpExport.objects.filter(workflow=workflow).order_by('-created_at')
    csv_exports = CSVExport.objects.filter(workflow=workflow).order_by('-created_at')
    join_reports = JoinReport.objects.filter(workflow=workflow).order_by('-created_at')
    hit_reports = SearchHitReport.objects.filter(workflow=workflow).order_by('-created_at')

    context = {
        'workflow': workflow,
        'geojson_exports': geojson_exports,
        'shp_exports': shp_exports,
        'csv_exports': csv_exports,
        'join_reports': join_reports,
        'hit_reports': hit_reports,
        'last_update': last_update,
        'subject_count': subjects.count(),
        'covenants_count': subjects.filter(bool_covenant=True).count(),
        'covenants_maybe_count': subjects.filter(bool_covenant=None).count(),
        'mapped_count': mapped_count
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
