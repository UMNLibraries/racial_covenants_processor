from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
import json

from django.conf import settings
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.contrib.gis.geos.error import GEOSException
from django.db.models import (
    Case,
    Count,
    IntegerField,
    Max,
    OuterRef,
    Q,
    Subquery,
    TextField,
    Value,
    When,
)
from django.db.models.functions import Cast, Length
from apps.deed.models import SearchHitReport
from apps.zoon.models import (
    MANUAL_COV_OPTIONS,
    MATCH_TYPE_OPTIONS,
    ManualCovenant,
    ManualCovenantParcelPINLink,
    ManualParcelPINLink,
    ZooniverseWorkflow,
    ZooniverseSubject,
)
from apps.parcel.models import (
    GeoJSONExport,
    ShpExport,
    CSVExport,
    AllCovenantedDocsCSVExport,
    DischargeCSVExport,
    UnmappedCSVExport,
    ValidationCSVExport,
    JoinReport,
    CovenantDrawnGeometry,
    Parcel,
    CovenantedParcel,
    ParcelPMTilesExport,
    ParcelSearchIndex,
    PMTilesExport,
)


@login_required(login_url="/admin/login/")
def index(request):
    last_update_subquery = (
        ZooniverseSubject.objects.filter(workflow=OuterRef("pk"))
        .values("workflow")
        .annotate(last=Max("date_updated"))
        .values("last")
    )

    mapped_count_subquery = (
        Parcel.covenant_objects.filter(workflow=OuterRef("pk"))
        .values("workflow")
        .annotate(cnt=Count("id"))
        .values("cnt")
    )

    workflows = ZooniverseWorkflow.objects.annotate(
        last_update=Subquery(last_update_subquery),
        mapped_count=Subquery(mapped_count_subquery),
    ).order_by("workflow_name")

    context = {
        "all_workflows": workflows,
        "workflow_cards": [
            {
                "obj": w,
                "last_update": w.last_update,
                "mapped_count": w.mapped_count or 0,
            }
            for w in workflows
        ],
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

    # PMTiles exports
    pmtiles_exports = PMTilesExport.objects.filter(workflow=workflow).order_by(
        "-created_at"
    )
    first_pmtiles = pmtiles_exports.first()
    pmtiles_url = first_pmtiles.pmtiles.url if first_pmtiles else None

    export_sections.append(
        {
            "title": "Download in-progress PMTiles exports",
            "exports": [
                {
                    "url": exp.pmtiles.url,
                    "created": exp.created_at,
                    "count": exp.covenant_count,
                    "label": "mapped covenants",
                }
                for exp in pmtiles_exports
            ],
        }
    )

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

    all_discharges = DischargeCSVExport.objects.filter(workflow=workflow).order_by(
        "-created_at"
    )
    export_sections.append(
        {
            "title": "Download all discharge CSVs",
            "exports": [
                {
                    "url": exp.csv.url,
                    "created": exp.created_at,
                    "count": exp.doc_count,
                    "label": "discharge CSVs",
                }
                for exp in all_discharges
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

    context = {
        "workflow": workflow,
        "export_sections": export_sections,
        "pmtiles_url": pmtiles_url,
        "last_update": last_update,
        "subject_count": subjects.count(),
        "covenants_count": subjects.filter(bool_covenant_final=True).count(),
        "covenants_maybe_count": subjects.filter(bool_covenant_final=None).count(),
        "mapped_count": mapped_count,
        "all_workflows": all_workflows,
    }
    return context


def generate_workflow_summary_chart_data(request, workflow):
    deed_year_data = list(
        CovenantedParcel.objects.filter(workflow=workflow, deed_year__isnull=False)
        .values("deed_year")
        .annotate(count=Count("id"))
        .order_by("deed_year")
    )

    city_data = list(
        CovenantedParcel.objects.filter(workflow=workflow, deed_year__isnull=False)
        .values("city")
        .annotate(count=Count("id"))
        .order_by("city")
    )

    return {
        "deed_year_data_json": json.dumps(deed_year_data),
        "city_data_json": json.dumps(city_data),
    }


@login_required(login_url="/admin/login/")
def workflow_summary(request, workflow_id):
    workflow = ZooniverseWorkflow.objects.get(id=workflow_id)

    summary = generate_workflow_summary_context(request, workflow)
    charts = generate_workflow_summary_chart_data(request, workflow)

    context = summary | charts

    return render(request, "workflow_summary.html", context)


@login_required(login_url="/admin/login/")
def workflow_summary_slug(request, workflow_slug):
    workflow = ZooniverseWorkflow.objects.get(slug=workflow_slug)

    summary = generate_workflow_summary_context(request, workflow)
    charts = generate_workflow_summary_chart_data(request, workflow)

    context = summary | charts

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


COVENANT_SEARCH_LIMIT = 50

# The record type is only ever Zooniverse or manual; the sub-type is what says
# why a covenant is hard to place -- "Long phys description" and "Something
# else" are the ones that tend to need a drawn shape.
MATCH_TYPE_LABELS = dict(MATCH_TYPE_OPTIONS)
MANUAL_COV_LABELS = dict(MANUAL_COV_OPTIONS)


def join_string_list(join_candidates):
    """The join strings a covenant would match a parcel on.

    This is what tells a user which parcel a covenant belongs to, so the editor
    leads with it.
    """
    if not join_candidates:
        return []
    return [c["join_string"] for c in join_candidates if c.get("join_string")]


def unmapped_covenant_querysets(workflow_id):
    """Confirmed covenants in this workflow with no parcel match yet, ordered
    so the ones a user can actually place -- those with join candidates -- come
    first, and those with no addition transcribed sink below those that have
    one (an empty addition would otherwise sort first and fill the page).
    join_candidates is a JSONField with no text lookups of its own, so it is
    cast to text for both the ordering and the search."""
    joins_text = Cast("join_candidates", TextField())
    # '[]', 'null' and '""' all mean no candidates
    no_joins = Case(
        When(joins_len__gt=2, then=Value(0)),
        default=Value(1),
        output_field=IntegerField(),
    )

    subjects = (
        ZooniverseSubject.unmapped_objects.filter(workflow_id=workflow_id)
        .annotate(joins_text=joins_text)
        .annotate(joins_len=Length("joins_text"))
        .annotate(no_joins=no_joins)
        .annotate(
            no_addition=Case(
                When(addition_final="", then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        .order_by(
            "no_joins", "no_addition", "addition_final", "block_final", "lot_final"
        )
    )
    manual_covs = (
        ManualCovenant.objects.filter(
            workflow_id=workflow_id, bool_confirmed=True, bool_parcel_match=False
        )
        .annotate(joins_text=joins_text)
        .annotate(joins_len=Length("joins_text"))
        .annotate(no_joins=no_joins)
        .annotate(
            no_addition=Case(
                When(addition="", then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        .order_by("no_joins", "no_addition", "addition", "block", "lot")
    )

    return subjects, manual_covs


def search_unmapped_covenants(workflow_id, query="", limit=COVENANT_SEARCH_LIMIT):
    """Search unmapped covenants. Runs here rather than in the browser: the
    largest workflow has thousands of them, and shipping them all made the
    editor slow to open. covenant_text is left out -- nothing displays it."""
    subjects, manual_covs = unmapped_covenant_querysets(workflow_id)

    if query:
        subjects = subjects.filter(
            Q(joins_text__icontains=query)
            | Q(addition_final__icontains=query)
            | Q(block_final__icontains=query)
            | Q(lot_final__icontains=query)
            | Q(deedpage_doc_num__icontains=query)
            | Q(seller_final__icontains=query)
            | Q(buyer_final__icontains=query)
        )
        manual_covs = manual_covs.filter(
            Q(joins_text__icontains=query)
            | Q(addition__icontains=query)
            | Q(block__icontains=query)
            | Q(lot__icontains=query)
            | Q(doc_num__icontains=query)
            | Q(seller__icontains=query)
            | Q(buyer__icontains=query)
        )

    results = [
        {
            "type": "zooniverse",
            "id": subject.pk,
            "addition": subject.addition_final,
            "block": subject.block_final,
            "lot": subject.lot_final,
            "doc_num": subject.deedpage_doc_num,
            "deed_date": subject.deed_date_final.isoformat()
            if subject.deed_date_final
            else None,
            "seller": subject.seller_final,
            "buyer": subject.buyer_final,
            "join_strings": join_string_list(subject.join_candidates),
            "match_type": MATCH_TYPE_LABELS.get(subject.match_type_final),
        }
        for subject in subjects[: limit + 1]
    ]

    if len(results) <= limit:
        results.extend(
            {
                "type": "manual",
                "id": cov.pk,
                "addition": cov.addition,
                "block": cov.block,
                "lot": cov.lot,
                "doc_num": cov.doc_num,
                "deed_date": cov.deed_date.isoformat() if cov.deed_date else None,
                "seller": cov.seller,
                "buyer": cov.buyer,
                "join_strings": join_string_list(cov.join_candidates),
                "match_type": MANUAL_COV_LABELS.get(cov.cov_type),
            }
            for cov in manual_covs[: limit + 1 - len(results)]
        )

    truncated = len(results) > limit
    return results[:limit], truncated


@login_required(login_url="/admin/login/")
def workflow_covenant_search(request, workflow_id):
    """Unmapped covenants matching a search, for the map editor's picker."""
    # No workflow lookup: it would be another round trip, and an id that does
    # not exist simply matches nothing
    query = request.GET.get("q", "").strip()

    results, truncated = search_unmapped_covenants(workflow_id, query)

    # Counting costs two more round trips, so it happens on the unfiltered
    # first load only -- that total is what the sidebar reports from then on
    total = (
        None
        if query
        else sum(qs.count() for qs in unmapped_covenant_querysets(workflow_id))
    )

    return JsonResponse(
        {
            "results": results,
            "truncated": truncated,
            "limit": COVENANT_SEARCH_LIMIT,
            "total": total,
        }
    )


@login_required(login_url="/admin/login/")
def workflow_map_edit(request, workflow_id):
    workflow = get_object_or_404(ZooniverseWorkflow, pk=workflow_id)

    latest_pmtiles = (
        PMTilesExport.objects.filter(workflow=workflow).order_by("-created_at").first()
    )
    latest_parcel_pmtiles = (
        ParcelPMTilesExport.objects.filter(workflow=workflow)
        .order_by("-created_at")
        .first()
    )
    latest_parcel_index = (
        ParcelSearchIndex.objects.filter(workflow=workflow)
        .order_by("-created_at")
        .first()
    )

    context = {
        "workflow": workflow,
        "pmtiles_url": latest_pmtiles.pmtiles.url if latest_pmtiles else None,
        "parcel_pmtiles_url": latest_parcel_pmtiles.pmtiles.url
        if latest_parcel_pmtiles
        else None,
        "parcel_index_url": latest_parcel_index.index_file.url
        if latest_parcel_index
        else None,
        "all_workflows": ZooniverseWorkflow.objects.all(),
    }

    return render(request, "workflow_map_edit.html", context)


MAX_DRAWN_FEATURES = 25


def drawn_feature_to_multipolygon(feature):
    """A GeoJSON feature from the map editor's drawing tools, as a MultiPolygon.

    CovenantedParcel.geom_4326 is a MultiPolygonField, so a single polygon is
    wrapped. Lines and points are refused: a covenant covers ground.
    """
    geometry = feature.get("geometry") if isinstance(feature, dict) else None
    if not geometry:
        raise ValueError("Each drawn shape needs a GeoJSON geometry.")

    try:
        geom = GEOSGeometry(json.dumps(geometry), srid=4326)
    except (GEOSException, GDALException, ValueError, TypeError):
        # GEOS and GDAL each reject malformed GeoJSON with their own exception
        raise ValueError("A drawn shape could not be read as GeoJSON.")

    if isinstance(geom, Polygon):
        geom = MultiPolygon(geom, srid=4326)
    elif not isinstance(geom, MultiPolygon):
        raise ValueError(
            f"Drawn shapes must be polygons; got {geom.geom_type.lower()}."
        )

    if not geom.valid:
        raise ValueError("A drawn shape is not a valid polygon.")

    return geom


@login_required(login_url="/admin/login/")
@require_POST
def workflow_link_covenant_parcels(request, workflow_id):
    """Join a covenant to the parcels a user picked on the map editor, and to
    any shapes they drew for ground no parcel covers.

    Parcel links are made with the same PIN link models the admin uses, so
    saving the covenant afterward runs the normal routine: rebuild parcel
    matches, flag the parcels as covenanted, rebuild the flat CovenantedParcel
    rows and fire off the PMTiles bake Lambda. Drawn shapes are additive rather
    than an alternative -- a covenant can cover parcels and drawn ground at
    once -- and each becomes its own flat row through its own save signal.
    """
    workflow = get_object_or_404(ZooniverseWorkflow, pk=workflow_id)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    covenant_type = payload.get("covenant_type")
    if covenant_type not in ("zooniverse", "manual"):
        return JsonResponse(
            {"detail": "covenant_type must be 'zooniverse' or 'manual'."}, status=400
        )

    try:
        covenant_id = int(payload.get("covenant_id"))
        parcel_ids = [int(pk) for pk in payload.get("parcel_ids", [])]
    except (TypeError, ValueError):
        return JsonResponse(
            {"detail": "covenant_id and parcel_ids must be integers."}, status=400
        )

    drawn_features = payload.get("drawn_features") or []
    if not isinstance(drawn_features, list):
        return JsonResponse(
            {"detail": "drawn_features must be a list of GeoJSON features."},
            status=400,
        )
    if len(drawn_features) > MAX_DRAWN_FEATURES:
        return JsonResponse(
            {"detail": f"No more than {MAX_DRAWN_FEATURES} shapes at a time."},
            status=400,
        )

    if not parcel_ids and not drawn_features:
        return JsonResponse(
            {"detail": "Select at least one parcel or draw a shape."}, status=400
        )

    try:
        drawn_geoms = [drawn_feature_to_multipolygon(f) for f in drawn_features]
    except ValueError as err:
        return JsonResponse({"detail": str(err)}, status=400)

    parcels = Parcel.objects.filter(workflow=workflow, pk__in=parcel_ids)
    if parcels.count() != len(set(parcel_ids)):
        return JsonResponse(
            {"detail": "One or more parcels are not in this workflow."}, status=400
        )

    pins = sorted({p.pin_primary for p in parcels if p.pin_primary})
    no_pin_count = parcels.count() - len(
        [p for p in parcels if p.pin_primary]
    )
    if parcel_ids and not pins:
        return JsonResponse(
            {
                "detail": "None of the selected parcels have a primary PIN, "
                "which is what covenants are linked by."
            },
            status=400,
        )

    comment = f"Linked in the map editor by {request.user}"

    if covenant_type == "zooniverse":
        covenant = get_object_or_404(
            ZooniverseSubject, pk=covenant_id, workflow=workflow
        )
        existing_pins = set(
            ManualParcelPINLink.objects.filter(
                zooniverse_subject=covenant
            ).values_list("parcel_pin", flat=True)
        )
        # bulk_create rather than save() per link: each link's save() re-saves the
        # subject, and that rebuilds a workflow-wide parcel lookup every time.
        ManualParcelPINLink.objects.bulk_create(
            [
                ManualParcelPINLink(
                    workflow=workflow,
                    zooniverse_subject=covenant,
                    zoon_workflow_id=workflow.zoon_id,
                    zoon_subject_id=covenant.zoon_subject_id,
                    parcel_pin=pin,
                    comments=comment,
                )
                for pin in pins
                if pin not in existing_pins
            ]
        )
    else:
        covenant = get_object_or_404(ManualCovenant, pk=covenant_id, workflow=workflow)
        existing_pins = set(
            ManualCovenantParcelPINLink.objects.filter(
                manual_covenant=covenant
            ).values_list("parcel_pin", flat=True)
        )
        ManualCovenantParcelPINLink.objects.bulk_create(
            [
                ManualCovenantParcelPINLink(
                    workflow=workflow,
                    manual_covenant=covenant,
                    parcel_pin=pin,
                    comments=comment,
                )
                for pin in pins
                if pin not in existing_pins
            ]
        )

    # Each save() rebuilds that shape's flat row and re-bakes; the covenant
    # save below does the same for parcel matches.
    for geom in drawn_geoms:
        CovenantDrawnGeometry.objects.create(
            workflow=workflow,
            zooniverse_subject=covenant if covenant_type == "zooniverse" else None,
            manual_covenant=covenant if covenant_type == "manual" else None,
            geom_4326=geom,
            comments=comment,
            added_by=str(request.user),
        )

    # Rebuilds parcel matches, flat covenants and dispatches the PMTiles bake.
    covenant.save()
    covenant.refresh_from_db()

    matched_parcel_pks = list(covenant.parcel_matches.values_list("pk", flat=True))
    covenanted_parcels = CovenantedParcel.objects.filter(
        workflow=workflow, parcel__pk__in=matched_parcel_pks
    )
    drawn_rows = CovenantedParcel.objects.filter(
        workflow=workflow,
        drawn_geometry__in=CovenantDrawnGeometry.objects.filter(
            **{
                "zooniverse_subject" if covenant_type == "zooniverse" else "manual_covenant": covenant
            }
        ),
    )

    return JsonResponse(
        {
            "covenant_type": covenant_type,
            "covenant_id": covenant.pk,
            "pins_linked": pins,
            "parcels_without_pin": no_pin_count,
            "matched_parcel_count": len(matched_parcel_pks),
            "covenanted_parcel_count": covenanted_parcels.count(),
            "drawn_shapes_saved": len(drawn_geoms),
            "drawn_shape_count": drawn_rows.count(),
            "pmtiles_bake_dispatched": bool(settings.PMTILES_LAMBDA_NAME),
        }
    )
