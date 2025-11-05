from django.shortcuts import render, redirect
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.auth.decorators import login_required

from django.db.models import Max, Count
from apps.deed.models import SearchHitReport
from apps.zoon.models import ZooniverseWorkflow, ZooniverseSubject
from apps.parcel.models import (
    GeoJSONExport,
    ShpExport,
    CSVExport,
    AllCovenantedDocsCSVExport,
    UnmappedCSVExport,
    ValidationCSVExport,
    JoinReport,
    Parcel,
    CovenantedParcel,
)


@login_required(login_url="/admin/login/")
def index(request):
    workflows = ZooniverseWorkflow.objects.all()
    context = {
        "all_workflows": workflows,
    }
    return render(request, "index.html", context)


@login_required(login_url="/admin/login/")
def zoon_subject_lookup(request, zoon_subject_id):
    try:
        subject = ZooniverseSubject.objects.get(zoon_subject_id=zoon_subject_id)
        response = redirect(f"/admin/zoon/zooniversesubject/{subject.pk}/change/")
        return response
    except:
        raise


def generate_workflow_summary_context(request, workflow):
    subjects = ZooniverseSubject.objects.filter(workflow=workflow)
    last_update = subjects.aggregate(last_update=Max("date_updated"))["last_update"]

    mapped_count = Parcel.covenant_objects.filter(workflow=workflow).count()

    # Create standardized export format with url, created, count, label
    export_sections = []

    # GeoJSON exports
    geojson_exports = GeoJSONExport.objects.filter(workflow=workflow).order_by(
        "-created_at"
    )
    export_sections.append(
        {
            "title": "Download in-progress geoJSONs",
            "exports": [
                {
                    "url": exp.geojson.url,
                    "created": exp.created_at,
                    "count": exp.covenant_count,
                    "label": "mapped covenants",
                }
                for exp in geojson_exports
            ],
        }
    )

    # Shapefile exports
    shp_exports = ShpExport.objects.filter(workflow=workflow).order_by("-created_at")
    export_sections.append(
        {
            "title": "Download in-progress shapefiles",
            "exports": [
                {
                    "url": exp.shp_zip.url,
                    "created": exp.created_at,
                    "count": exp.covenant_count,
                    "label": "mapped covenants",
                }
                for exp in shp_exports
            ],
        }
    )

    # CSV exports
    csv_exports = CSVExport.objects.filter(workflow=workflow).order_by("-created_at")
    export_sections.append(
        {
            "title": "Download in-progress CSVs",
            "exports": [
                {
                    "url": exp.csv.url,
                    "created": exp.created_at,
                    "count": exp.covenant_count,
                    "label": "mapped covenants",
                }
                for exp in csv_exports
            ],
        }
    )

    # All covenanted docs CSVs
    all_covenanted_docs = AllCovenantedDocsCSVExport.objects.filter(
        workflow=workflow
    ).order_by("-created_at")
    export_sections.append(
        {
            "title": "Download all covenanted docs CSVs",
            "exports": [
                {
                    "url": exp.csv.url,
                    "created": exp.created_at,
                    "count": exp.doc_count,
                    "label": "covenanted docs",
                }
                for exp in all_covenanted_docs
            ],
        }
    )

    # Unmapped CSVs
    unmapped_exports = UnmappedCSVExport.objects.filter(workflow=workflow).order_by(
        "-created_at"
    )
    export_sections.append(
        {
            "title": "Download unmapped CSVs",
            "exports": [
                {
                    "url": exp.csv.url,
                    "created": exp.created_at,
                    "count": exp.covenant_count,
                    "label": "unmapped subjects",
                }
                for exp in unmapped_exports
            ],
        }
    )

    # Validation CSVs
    validation_exports = ValidationCSVExport.objects.filter(workflow=workflow).order_by(
        "-created_at"
    )
    export_sections.append(
        {
            "title": "Download validation CSVs",
            "exports": [
                {
                    "url": exp.csv.url,
                    "created": exp.created_at,
                    "count": exp.covenant_count,
                    "label": "retired Zooniverse subjects",
                }
                for exp in validation_exports
            ],
        }
    )

    # Join reports
    join_reports = JoinReport.objects.filter(workflow=workflow).order_by("-created_at")
    export_sections.append(
        {
            "title": "Download past join reports",
            "exports": [
                {
                    "url": exp.report_csv.url,
                    "created": exp.created_at,
                    "count": exp.covenanted_doc_count,
                    "label": "covenants",
                }
                for exp in join_reports
            ],
        }
    )

    # OCR hit reports
    hit_reports = SearchHitReport.objects.filter(workflow=workflow).order_by(
        "-created_at"
    )
    export_sections.append(
        {
            "title": "Download OCR hit reports",
            "exports": [
                {
                    "url": exp.report_csv.url,
                    "created": exp.created_at,
                    "count": exp.num_hits,
                    "label": "OCR hits",
                }
                for exp in hit_reports
            ],
        }
    )

    all_workflows = ZooniverseWorkflow.objects.all()

    # Get CovenantedParcel objects grouped by deed_year
    deed_year_data = (
        CovenantedParcel.objects.filter(workflow=workflow, deed_year__isnull=False)
        .values('deed_year')
        .annotate(count=Count('id'))
        .order_by('deed_year')
    )

    deed_years = [item['deed_year'] for item in deed_year_data]
    deed_year_counts = [item['count'] for item in deed_year_data]

    context = {
        "workflow": workflow,
        "export_sections": export_sections,
        "last_update": last_update,
        "subject_count": subjects.count(),
        "covenants_count": subjects.filter(bool_covenant=True).count(),
        "covenants_maybe_count": subjects.filter(bool_covenant=None).count(),
        "mapped_count": mapped_count,
        "all_workflows": all_workflows,
        "deed_years": deed_years,
        "deed_year_counts": deed_year_counts,
    }
    return context


@login_required(login_url="/admin/login/")
def workflow_summary(request, workflow_id):
    workflow = ZooniverseWorkflow.objects.get(id=workflow_id)

    context = generate_workflow_summary_context(request, workflow)

    return render(request, "workflow_summary.html", context)


@login_required(login_url="/admin/login/")
def workflow_summary_slug(request, workflow_slug):
    workflow = ZooniverseWorkflow.objects.get(slug=workflow_slug)

    context = generate_workflow_summary_context(request, workflow)

    return render(request, "workflow_summary.html", context)


@login_required(login_url="/admin/login/")
def covenant_matches(request, workflow_id):
    workflow = ZooniverseWorkflow.objects.get(id=workflow_id)
    covenants = (
        ZooniverseSubject.objects.filter(workflow=workflow, bool_covenant_final=True)
        .annotate(
            matched_parcel_join_strings=ArrayAgg(
                "parcel_matches__parceljoincandidate__join_string"
            )
        )
        .order_by("addition_final")
    )

    context = {
        "workflow": workflow,
        "covenants": covenants,
        "all_workflows": ZooniverseWorkflow.objects.all(),
    }

    return render(request, "covenant_matches.html", context)
