import os
import datetime
import tempfile
import subprocess
import geopandas as gpd
from zipfile import ZipFile

from django.core.management.base import BaseCommand
from django.core.files.base import File
from django.conf import settings

from apps.parcel.models import ShpExport, PMTilesExport
from apps.parcel.utils.export_utils import build_gdf
from apps.zoon.utils.zooniverse_config import get_workflow_obj


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

    def convert_to_pmtiles(self, gdf, geojson_path, pmtiles_path, version_slug):
        """Convert GeoDataFrame to PMTiles format using tippecanoe"""
        # Ensure GeoDataFrame has proper CRS (EPSG:4326 required for PMTiles)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        # Export to GeoJSON first
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
                    "0",  # min zoom
                    "-z",
                    "18",  # max zoom
                    "-l",
                    version_slug,  # layer name
                    geojson_path,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            print(f"PMTiles created successfully: {pmtiles_path}")

        except subprocess.CalledProcessError as e:
            print(f"Error creating PMTiles: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            raise
        except FileNotFoundError:
            print("Error: tippecanoe not found. Please install tippecanoe:")
            print("  macOS: brew install tippecanoe")
            print("  Linux: https://github.com/felt/tippecanoe")
            raise

    def save_pmtiles_local(self, gdf, version_slug):
        """Export GeoDataFrame to PMTiles format and save locally"""

        os.makedirs(
            os.path.join(settings.BASE_DIR, "data", "main_exports", version_slug),
            exist_ok=True,
        )

        geojson_path = os.path.join(
            settings.BASE_DIR,
            "data",
            "main_exports",
            version_slug,
            f"{version_slug}.geojson",
        )
        out_pmtiles = os.path.join(
            settings.BASE_DIR,
            "data",
            "main_exports",
            version_slug,
            f"{version_slug}.pmtiles",
        )

        self.convert_to_pmtiles(gdf, geojson_path, out_pmtiles, version_slug)

        # Clean up temporary GeoJSON
        if os.path.exists(geojson_path):
            os.remove(geojson_path)

        return out_pmtiles

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

    def generate_pmtiles_tmp(self, gdf, version_slug, workflow, created_at):
        """Convert GeoDataFrame to PMTiles and save to S3"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            geojson_path = os.path.join(tmp_dir, f"{version_slug}.geojson")
            pmtiles_path = os.path.join(tmp_dir, f"{version_slug}.pmtiles")

            # Convert to PMTiles using shared method
            self.convert_to_pmtiles(gdf, geojson_path, pmtiles_path, version_slug)

            # Create PMTilesExport object and save to S3
            pmtiles_export_obj = PMTilesExport(
                workflow=workflow, covenant_count=gdf.shape[0], created_at=created_at
            )

            with open(pmtiles_path, "rb") as f:
                pmtiles_export_obj.pmtiles.save(f"{version_slug}.pmtiles", File(f))
            pmtiles_export_obj.save()
            return pmtiles_export_obj

    def handle(self, *args, **kwargs):
        workflow_name = kwargs["workflow"]
        if not workflow_name:
            print("Missing workflow name. Please specify with --workflow.")
        else:
            workflow = get_workflow_obj(workflow_name)

            covenants_geo_df = build_gdf(workflow)

            print(covenants_geo_df)

            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M")
            version_slug = f"{workflow.slug}_covenants_{timestamp}"

            if kwargs["pmtiles"]:
                # Export to PMTiles format
                if kwargs["local"]:
                    pmtiles_path = self.save_pmtiles_local(covenants_geo_df, version_slug)
                    print(f"PMTiles saved to: {pmtiles_path}")
                else:
                    pmtiles_export_obj = self.generate_pmtiles_tmp(
                        covenants_geo_df, version_slug, workflow, now
                    )
                    print(f"PMTiles export object created: {pmtiles_export_obj}")
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
