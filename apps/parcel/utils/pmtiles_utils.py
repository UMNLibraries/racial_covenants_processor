import datetime
import json
import os
import subprocess
import tempfile

import boto3
from django.conf import settings
from django.core.files.base import File


def convert_to_pmtiles(
    gdf,
    geojson_path,
    pmtiles_path,
    layer_name,
    min_zoom=0,
    max_zoom=18,
    drop_densest=True,
):
    """Bake a GeoDataFrame to PMTiles with tippecanoe.

    drop_densest lets tippecanoe thin dense tiles to stay under its size limit,
    which is fine for a display layer. A layer that gets clicked on -- the map
    editor's parcels -- has to pass drop_densest=False, because a dropped
    feature is a parcel nobody can select.
    """
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    gdf.to_file(geojson_path, driver="GeoJSON")

    density_args = (
        ["--drop-densest-as-needed", "--extend-zooms-if-still-dropping"]
        if drop_densest
        else ["--no-tile-size-limit", "--no-feature-limit"]
    )

    try:
        subprocess.run(
            [
                "tippecanoe",
                "-o",
                pmtiles_path,
                "--force",
                *density_args,
                "-Z",
                str(min_zoom),
                "-z",
                str(max_zoom),
                "-l",
                layer_name,
                geojson_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("Error: tippecanoe not found. Please install tippecanoe:")
        print("  macOS: brew install tippecanoe")
        print("  Linux: https://github.com/felt/tippecanoe")
        raise


def save_pmtiles_local(gdf, version_slug, layer_name, **tippecanoe_options):
    out_dir = os.path.join(settings.BASE_DIR, "data", "main_exports", version_slug)
    os.makedirs(out_dir, exist_ok=True)

    geojson_path = os.path.join(out_dir, f"{version_slug}.geojson")
    out_pmtiles = os.path.join(out_dir, f"{version_slug}.pmtiles")

    convert_to_pmtiles(
        gdf, geojson_path, out_pmtiles, layer_name, **tippecanoe_options
    )

    if os.path.exists(geojson_path):
        os.remove(geojson_path)

    return out_pmtiles


def save_pmtiles_export(
    gdf, workflow, version_slug, layer_name, created_at, **tippecanoe_options
):
    """Bake a PMTiles file in a temp dir and store it on a ParcelPMTilesExport.

    Parcel tiles are baked here rather than in the Lambda: the Lambda exists to
    re-bake covenants on every save, while parcel boundaries change rarely
    enough to re-bake by hand.
    """
    from apps.parcel.models import ParcelPMTilesExport

    with tempfile.TemporaryDirectory() as tmp_dir:
        geojson_path = os.path.join(tmp_dir, f"{version_slug}.geojson")
        pmtiles_path = os.path.join(tmp_dir, f"{version_slug}.pmtiles")

        convert_to_pmtiles(
            gdf, geojson_path, pmtiles_path, layer_name, **tippecanoe_options
        )

        export_obj = ParcelPMTilesExport(
            workflow=workflow, parcel_count=gdf.shape[0], created_at=created_at
        )
        with open(pmtiles_path, "rb") as f:
            export_obj.pmtiles.save(f"{version_slug}.pmtiles", File(f))
        export_obj.save()

    return export_obj


def trigger_pmtiles_export(workflow):
    """Fire-and-forget async invoke of the PMTiles bake Lambda."""
    if not settings.PMTILES_LAMBDA_NAME:
        return None

    request_id = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    boto3.client("lambda", region_name=settings.AWS_S3_REGION_NAME).invoke(
        FunctionName=settings.PMTILES_LAMBDA_NAME,
        InvocationType="Event",
        Payload=json.dumps(
            {
                "workflow_id": workflow.pk,
                "workflow_slug": workflow.slug,
                "request_id": request_id,
            }
        ),
    )
    return request_id
