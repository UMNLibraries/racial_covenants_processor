# Racial Covenants Processor

This is the roadmap and future home for a generalized set of tools to OCR property deeds to look for racially restrictive covenant language, then map the results.

Current collaborators include Nicholas Boren, Michael Corey and Justin Schell.

## Software requirements
- Tesseract OCR engine
- geos and gdal
- pytesseract
- pandas
- pipenv
- PostGIS/PostgreSQL

## Note on legacy code
The "deeds" app is currently not being used, except to port over the legacy classification system for comparison with the new Zooniverse-native methods

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
python manage.py load_zooniverse_export
```
  - Side effect: Stats on hit rate, false positives, etc.
1. Automated join of matches to modern parcel map
1. Export list of unmatched confirmed covenants
1. Manual (GUIish?) cleanup of bad joins, split parcels, etc.
1. Metes and bounds manual tracing
1. Final shapefile/data layer

## Other workflow elements
Manual corrections are stored as separate models from the ZooniverseSubject model so edits are non-destructive and can be recreated in case of a need to re-import from Zooniverse, or can be rolled back as new information emerges.
```
# To archive manual corrections in a CSV for later re-import:
python manage.py dump_manual_corrections --workflow "Ramsey County"

# To re-import a ManualCorrection csv export:
python manage.py load_manual_corrections --workflow "Ramsey County" --infile relative/path/to/file

# To manually re-join corrections to subjects (mostly you will never run this, it's run as a part of other scripts)
python manage.py connect_manual_corrections --workflow "Ramsey County"
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
