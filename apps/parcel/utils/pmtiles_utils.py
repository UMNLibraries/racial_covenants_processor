import datetime
import json
import os
import subprocess

import boto3
from django.conf import settings


def convert_to_pmtiles(gdf, geojson_path, pmtiles_path, layer_name):
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    gdf.to_file(geojson_path, driver="GeoJSON")

    try:
        subprocess.run(
            [
                "tippecanoe",
                "-o",
                pmtiles_path,
                "--force",
                "--drop-densest-as-needed",
                "--extend-zooms-if-still-dropping",
                "-Z",
                "0",
                "-z",
                "18",
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


def save_pmtiles_local(gdf, version_slug, layer_name):
    out_dir = os.path.join(settings.BASE_DIR, "data", "main_exports", version_slug)
    os.makedirs(out_dir, exist_ok=True)

    geojson_path = os.path.join(out_dir, f"{version_slug}.geojson")
    out_pmtiles = os.path.join(out_dir, f"{version_slug}.pmtiles")

    convert_to_pmtiles(gdf, geojson_path, out_pmtiles, layer_name)

    if os.path.exists(geojson_path):
        os.remove(geojson_path)

    return out_pmtiles


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
