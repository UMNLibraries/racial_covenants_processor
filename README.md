# Racial Covenants Processor

This is the roadmap and future home for a generalized set of tools to OCR property deeds to look for racially restrictive covenant language, then map the results.

Current collaborators include Nicholas Boren, Michael Corey and Justin Schell.

## Software requirements
- Tesseract OCR engine
- geos and gdal
- proj
- pytesseract
- pandas and geopandas
- pipenv
- PostGIS/PostgreSQL

## Note on legacy code
The "deed' app is currently not being used, except to port over the legacy classification system for comparison with the new Zooniverse-native methods

## High-level workflow

1. Identify deed image folder structure
1. Create manifest of multipage deed images to OCR
1. Split and OCR deed images
1. Export list of positive matches for racially restrictive language
  - Side effect: Create analyzable statistics on which language found
1. Upload images of positive matches or all tifs to private S3 for web formatting
```
python manage.py upload_deed_images --workflow "Ramsey County" --cache
python manage.py gather_deed_images --workflow "Ramsey County"
# To delete:
python manage.py delete_raw_images
```

1. Upload matching files to Zooniverse (or point to S3 images)
1. Upload batch of records to Zooniverse for community confirmation
1. Export batch results from Zooniverse (Using command line tools)
1. Load raw and aggregated Zooniverse responses into individual property matches
```
python manage.py load_zooniverse_export --workflow "Ramsey County"
```
  - Side effect: Stats on hit rate, false positives, etc.
1. Load modern parcel shapefiles with unique fields mapped to unified subset
```
python manage.py load_parcel_shp --workflow "Ramsey County"
```
1. Load images to s3 and/or list of plats/additions to help with autojoin to Parcels and with manual research
```
python manage.py upload_plat_images --workflow "Ramsey County"
python manage.py load_plat_records --workflow "Ramsey County"
```
1. Automated join of matches to modern parcel map
```
python manage.py rebuild_parcel_spatial_lookups --workflow "Ramsey County"
python manage.py rebuild_covenant_spatial_lookups --workflow "Ramsey County"
python manage.py match_parcels --workflow "Ramsey County"
```
1. Export list of unmatched confirmed covenants
1. Manual (GUIish?) cleanup of bad joins, split parcels, etc.
1. Metes and bounds manual tracing
1. Final shapefile/data layer
```
python manage.py dump_covenants_shapefile --workflow "Ramsey County"
```

## Other workflow elements
Manual corrections, extra parcel records and alternate names for plats are stored as separate models from the ZooniverseSubject model so edits are non-destructive and can be recreated in case of a need to re-import from Zooniverse, or can be rolled back as new information emerges.
```
# To archive manual entries in a CSV for later re-import:
python manage.py dump_manual_corrections --workflow "Ramsey County"
python manage.py dump_extra_parcels --workflow "Ramsey County"
python manage.py dump_plat_alternate_names --workflow "Ramsey County"

# To re-import a those manual entries from csv export:
python manage.py load_manual_corrections --workflow "Ramsey County" --infile relative/path/to/file
python manage.py load_extra_parcels --workflow "Ramsey County" --infile relative/path/to/file
python manage.py load_plat_alternate_names --workflow "Ramsey County" --infile relative/path/to/file

# To manually re-join corrections to subjects/plats (mostly you will never run these, which are run as a part of the previous "load" scripts)
python manage.py connect_manual_corrections --workflow "Ramsey County"
python manage.py connect_extra_parcels --workflow "Ramsey County"
python manage.py connect_plat_alternate_names --workflow "Ramsey County"
```

## Django installation process

### 1. Create a PostGIS-enabled database for the project
The psql command will vary slightly with different OSes. For Mac:
```
psql -d postgres

CREATE DATABASE racial_covenants_processor;
CREATE USER racial_covenants_processor with password 'racial_covenants_processor';
GRANT ALL PRIVILEGES ON DATABASE racial_covenants_processor to racial_covenants_processor;
\q
psql -d racial_covenants_processor
CREATE EXTENSION postgis;

```

### 2. Install Python environment
```
pipenv install
```

### 3. Create a Postgresql service to connect between Django and the DB
```
(.pg_service.conf)
[deeds_service]
host=localhost
user=racial_covenants_processor
dbname=racial_covenants_processor
port=5432
```

### 4. Sync Django with your database
```
pipenv shell
python manage.py migrate
```

### 5. To be able to view the admin pages, create a superuser
```python manage.py createsuperuser```
