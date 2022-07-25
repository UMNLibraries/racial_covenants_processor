# Racial Covenants Processor

This is the roadmap and future home for a generalized set of tools to OCR property deeds to look for racially restrictive covenant language, then map the results.

Current collaborators include Michael Corey, Justin Schell and Nicholas Boren.

## How to map a covenant

Once all of the below load scripts have been run, many covenants (ZooniverseSubject) objects will not automatically join to modern parcels. Here's how to try to make them match up.

1. Open the ZooniverseSubject list view.
1. Filter for "has racial covenant" (Yes) and "bool parcel match" (no) to find covenants that need mapping.
1. Select a ZooniverseSubject that looks potentially fixable (e.g. geo information that looks close, but not quite right)
1. Look at the individual responses at the bottom of the ZooniverseSubject page to see what different users entered, and compare to what is saved as the "Addition," "Block" and "Lot" values at the top.
1. If you see something to fix, click on the deed images to confirm that your fix is accurate.
1. Add a ManualCorrection, and enter in ONLY the values you want to change.
1. Click "save and continue editing"
1. Check to see if there are now values in the "Matching parcels" section. If yes, then at least part of the lot has matched to a modern Parcel. If not, there is either more to fix or an automatic match isn't possible.
1. Choose a "match type" value to indicate how this parcel was matched (or how it will need to be matched in the future).

## Software requirements
- Tesseract OCR engine
- geos and gdal
- proj
- pytesseract
- pandas and geopandas
- pipenv
- PostGIS/PostgreSQL
- AWS SAM for lambdas (separate repos)

## High-level workflow
1. Start new config entry in local_settings.py
```
ZOONIVERSE_QUESTION_LOOKUP = {
    'WI Milwauke County': {
    },
    'Ramsey County': {
      ...
    }
  }
```
1. Identify deed image folder structure and add glob and regex parameters to parse deed image metadata that can be gleaned from the filepath.
```
ZOONIVERSE_QUESTION_LOOKUP = {
    'WI Milwauke County': {
        'deed_image_raw_glob': 'D:/Milwaukee_Books/Images/**/*.tif',
        'deed_image_regex': r'\/(?P<workflow_slug>[A-z\-]+)\/(?P<doc_date>\d+)\/(?P<doc_num>\d+)_(?P<doc_type>[A-Z]+)_(?P<page_num>\d+)',
        'deed_image_raw_glob': 'D:/Milwaukee_Books/Images/**/*.tif',
    },
    'Ramsey County': {
      ...
    }
  }
```
1. Create workflow object
```
python manage.py create_workflow --workflow "WI Milwaukee County"
```
1. Upload deed images to private s3 bucket. This will trigger lambdas to OCR the text, generate basic document statistics, check for racial terms and to make web versions of the document images. (Side effect: Create analyzable statistics on which language found)
```
python manage.py upload_deed_images --workflow "WI Milwaukee County"
# To delete:
python manage.py delete_raw_images
```
1. Gather results of document image uploads into the Django app. Optionally, add supplemental info like missing doc nums that have been provided in a separate csv.
```
python manage.py gather_deed_images --workflow "WI Milwaukee County"
```
1. Gather list of positive matches for racially restrictive language and join to deed image records in Django app
```
TODO: python manage.py gather_image_hits --workflow "WI Milwaukee County"
```
1. Upload matching files to Zooniverse (or point to S3 images)
```
TODO
```
1. Upload batch of records to Zooniverse for community confirmation
```
TODO
```
1. Export batch results from Zooniverse (Using command line tools)
1. Load raw and aggregated Zooniverse responses into individual property matches
```
python manage.py load_zooniverse_export --slow --workflow "Ramsey County"
```
  - Side effect: Stats on hit rate, false positives, etc.
1. Join deed images to zooniverse subjects (hmm maybe not? we'll see later if it makes sense to create these before uploading to Zooniverse. But since you won't have a zoon subject ID maybe you don't need to.)
```
python manage.py join_deeds_to_subjects --workflow "Ramsey County"
```
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
ALTER DATABASE racial_covenants_processor OWNER TO racial_covenants_processor;
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
