import datetime
import os
import tempfile
from zipfile import ZipFile

import geopandas as gpd
from django.conf import settings
from django.core.files.base import File
from django.core.management.base import BaseCommand

from apps.parcel.models import ShpExport
from apps.parcel.utils.export_utils import (
    build_gdf,
    build_parcel_gdf,
    build_parcel_search_index,
)
from apps.parcel.utils.pmtiles_utils import (
    save_pmtiles_export,
    save_pmtiles_local,
    trigger_pmtiles_export,
)
from apps.parcel.utils.search_index_utils import (
    save_search_index_export,
    save_search_index_local,
)
from apps.zoon.utils.zooniverse_config import get_workflow_obj

PARCEL_TILES_MIN_ZOOM = 13
PARCEL_TILES_MAX_ZOOM = 16


class Command(BaseCommand):
    """Attempt to auto-join covenants to modern parcels using current values"""

    def add_arguments(self, parser):
        parser.add_argument(
            "-w",
            "--workflow",
            type=str,
            help='Name of Zooniverse workflow to process, e.g. "Ramsey County"',
        )
        parser.add_argument(
            "-l",
            "--local",
            action="store_true",
            help='Save to local un-zipped shp in "main_exports" dir, rather than Django object/S3',
        )
        parser.add_argument(
            "-p",
            "--pmtiles",
            action="store_true",
            help="Export to PMTiles format instead of shapefile",
        )
        parser.add_argument(
            "-s",
            "--parcel-search-index",
            action="store_true",
            help="Build the map editor's parcel search sidecar (join strings, PIN, "
            "address, centroid) for this workflow. Cheap -- no tiles are baked -- so "
            "it can be re-run on its own whenever parcels or join candidates change.",
        )
        parser.add_argument(
            "-a",
            "--all-parcels",
            action="store_true",
            help="Bake every parcel in the workflow rather than covenants only. Requires --pmtiles.",
        )

    def save_shp_local(self, gdf, version_slug, schema=None):
        os.makedirs(
            os.path.join(settings.BASE_DIR, "data", "main_exports", version_slug),
            exist_ok=True,
        )
        out_shp = os.path.join(
            settings.BASE_DIR,
            "data",
            "main_exports",
            version_slug,
            f"{version_slug}.shp",
        )

        gdf.to_file(out_shp, index=False, schema=schema)

        return out_shp

    def generate_zip_tmp(self, gdf, version_slug, workflow, created_at, schema=None):
        # Convert to shapefile and serve it to the user
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Export gdf as shapefile
            gdf.to_file(
                os.path.join(tmp_dir, f"{version_slug}.shp"),
                index=False,
                driver="ESRI Shapefile",
                schema=schema,
            )

            # Zip the exported files to a single file
            tmp_zip_file_name = f"{version_slug}.zip"
            tmp_zip_file_path = f"{tmp_dir}/{tmp_zip_file_name}"
            tmp_zip_obj = ZipFile(tmp_zip_file_path, "w")

            for file in os.listdir(tmp_dir):
                if file != tmp_zip_file_name:
                    tmp_zip_obj.write(os.path.join(tmp_dir, file), file)

            tmp_zip_obj.close()

            shp_export_obj = ShpExport(
                workflow=workflow, covenant_count=gdf.shape[0], created_at=created_at
            )

            # Using File
            with open(tmp_zip_file_path, "rb") as f:
                shp_export_obj.shp_zip.save(f"{version_slug}.zip", File(f))
            shp_export_obj.save()
            return shp_export_obj

    def dump_all_parcels(self, workflow, local=False):
        """Bake a PMTiles layer of every parcel in the workflow."""
        parcels_geo_df = build_parcel_gdf(workflow)

        if parcels_geo_df.shape[0] == 0:
            print(f"No parcels loaded for {workflow}, so there is nothing to bake.")
            return

        now = datetime.datetime.now()
        version_slug = f"{workflow.slug}_parcels_{now.strftime('%Y%m%d_%H%M')}"
        layer_name = f"{workflow.slug}_parcels"

        print(f"Baking {parcels_geo_df.shape[0]} parcels to PMTiles...")

        tippecanoe_options = {
            "min_zoom": PARCEL_TILES_MIN_ZOOM,
            "max_zoom": PARCEL_TILES_MAX_ZOOM,
            "drop_densest": False,
        }

        if local:
            pmtiles_path = save_pmtiles_local(
                parcels_geo_df, version_slug, layer_name, **tippecanoe_options
            )
            print(f"Parcel PMTiles saved to: {pmtiles_path}")
            return

        export_obj = save_pmtiles_export(
            parcels_geo_df,
            workflow,
            version_slug,
            layer_name,
            now,
            **tippecanoe_options,
        )
        print(f"Parcel PMTiles export object created: {export_obj.pmtiles.url}")

    def dump_parcel_search_index(self, workflow, local=False):
        """Build the map editor's parcel search sidecar."""
        print(f"Building parcel search index for {workflow}...")
        index = build_parcel_search_index(workflow)

        if len(index["parcels"]) == 0:
            print(f"No parcels loaded for {workflow}, so there is nothing to index.")
            return

        now = datetime.datetime.now()
        version_slug = (
            f"{workflow.slug}_parcel_search_{now.strftime('%Y%m%d_%H%M')}"
        )

        if local:
            index_path = save_search_index_local(index, version_slug)
            print(f"Parcel search index saved to: {index_path}")
            return

        export_obj = save_search_index_export(index, workflow, version_slug, now)
        print(
            f"Parcel search index created for {export_obj.parcel_count} parcels: "
            f"{export_obj.index_file.url}"
        )

    def handle(self, *args, **kwargs):
        workflow_name = kwargs["workflow"]
        if not workflow_name:
            print("Missing workflow name. Please specify with --workflow.")
        else:
            workflow = get_workflow_obj(workflow_name)

            if kwargs["all_parcels"]:
                if not kwargs["pmtiles"]:
                    print("--all-parcels requires --pmtiles.")
                    return
                self.dump_all_parcels(workflow, local=kwargs["local"])
                self.dump_parcel_search_index(workflow, local=kwargs["local"])
                return

            if kwargs["parcel_search_index"]:
                self.dump_parcel_search_index(workflow, local=kwargs["local"])
                return

            if kwargs["pmtiles"] and not kwargs["local"]:
                request_id = trigger_pmtiles_export(workflow)
                if request_id:
                    print(f"PMTiles bake dispatched to Lambda: {request_id}")
                else:
                    print("PMTILES_LAMBDA_NAME is not set, so no bake was dispatched.")
                return

            covenants_geo_df = build_gdf(workflow)

            print(covenants_geo_df)

            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M")
            version_slug = f"{workflow.slug}_covenants_{timestamp}"

            if kwargs["pmtiles"]:
                pmtiles_path = save_pmtiles_local(
                    covenants_geo_df, version_slug, workflow.slug
                )
                print(f"PMTiles saved to: {pmtiles_path}")
            elif kwargs["local"]:
                # Export to shapefile locally
                try:
                    schema = None
                    # Pyogrio doesn't allow schemas
                except:
                    # Shapefiles don't like datetime format, so if fiona, specify date in manual schema
                    schema = gpd.io.file.infer_schema(covenants_geo_df)
                    schema["properties"]["deed_date"] = "date"
                    schema["properties"]["dt_updated"] = "date"
                    schema["properties"]["zn_dt_ret"] = "date"

                shp_local = self.save_shp_local(covenants_geo_df, version_slug, schema)
                print(f"Shapefile saved to: {shp_local}")
            else:
                # Save to zipped shp in Django storages/model
                try:
                    schema = None
                    # Pyogrio doesn't allow schemas
                except:
                    # Shapefiles don't like datetime format, so if fiona, specify date in manual schema
                    schema = gpd.io.file.infer_schema(covenants_geo_df)
                    schema["properties"]["deed_date"] = "date"
                    schema["properties"]["dt_updated"] = "date"
                    schema["properties"]["zn_dt_ret"] = "date"

                shp_export_obj = self.generate_zip_tmp(
                    covenants_geo_df, version_slug, workflow, now, schema
                )
                print(f"Shapefile export object created: {shp_export_obj}")
