import datetime
import os
import subprocess
import tempfile

from django.conf import settings
from django.core.files.base import File

from apps.parcel.utils.export_utils import build_gdf


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


def save_pmtiles_local(gdf, version_slug):
    out_dir = os.path.join(settings.BASE_DIR, "data", "main_exports", version_slug)
    os.makedirs(out_dir, exist_ok=True)

    geojson_path = os.path.join(out_dir, f"{version_slug}.geojson")
    out_pmtiles = os.path.join(out_dir, f"{version_slug}.pmtiles")

    convert_to_pmtiles(gdf, geojson_path, out_pmtiles, version_slug)

    if os.path.exists(geojson_path):
        os.remove(geojson_path)

    return out_pmtiles


def build_pmtiles_export(workflow, gdf=None, created_at=None):
    from apps.parcel.models import PMTilesExport

    if gdf is None:
        gdf = build_gdf(workflow)
    if created_at is None:
        created_at = datetime.datetime.now()

    timestamp = created_at.strftime("%Y%m%d_%H%M")
    version_slug = f"{workflow.slug}_covenants_{timestamp}"

    with tempfile.TemporaryDirectory() as tmp_dir:
        geojson_path = os.path.join(tmp_dir, f"{version_slug}.geojson")
        pmtiles_path = os.path.join(tmp_dir, f"{version_slug}.pmtiles")

        convert_to_pmtiles(gdf, geojson_path, pmtiles_path, version_slug)

        pmtiles_export_obj = PMTilesExport(
            workflow=workflow,
            covenant_count=gdf.shape[0],
            created_at=created_at,
        )
        with open(pmtiles_path, "rb") as f:
            pmtiles_export_obj.pmtiles.save(f"{version_slug}.pmtiles", File(f))
        pmtiles_export_obj.save()
        return pmtiles_export_obj
