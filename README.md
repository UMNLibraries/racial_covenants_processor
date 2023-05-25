# Racial Covenants Processor

This is the main repository for The Deed Machine, a generalized set of tools to OCR property deeds to look for racially restrictive covenant language, then map the results.

The Deed Machine was created at Mapping Prejudice at the University of Minnesota Libraries. Current collaborators include Michael Corey, Justin Schell and Nicholas Boren.

The basic steps involved in the Deed Machine process for covenant identification and mapping are:

1. Image pre-processing and OCR
1. Term search
1. Hit collection
1. Zooniverse upload
1. Zooniverse transcription
1. Zooniverse post-processing
1. Covenant mapping
1. Data distribution

## How to manually map or clean up a covenant

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
1. If you need to map lots across more than one block, add ExtraParcelCandidate objects for each additional block or lot range. ONLY ONE ManualCorrection OBJECT should be added per ZooniverseSubject.

## Software requirements
- geos and gdal
- proj
- pandas and geopandas
- pipenv
- PostGIS/PostgreSQL
- AWS SAM for lambdas (separate repos)
- libmagic (mostly to silence panoptes/zooniverse warnings)

## Downloading new batches of Zooniverse results
1. Export updated manual corrections in case something goes wrong, though you generally won't need to reload these (just re-join) unless your database needs to be completely rebuilt
```
python manage.py dump_manual_corrections --workflow "WI Milwaukee County"
python manage.py dump_extra_parcels --workflow "WI Milwaukee County"
```
1. Create and download a fresh Zooniverse export from the Zooniverse Lab tab.  
    A. Click Lab > Data Exports > Request new workflow classification export  
    B. Click Lab > Data Exports > Request new workflow export  
    C. Download files once notified by email.  
    D. Place downloaded files in `racial_covenants_processor/racial_covenants_processor/data/zooniverse_exports/your-workflow-slug/`  
    E. If necessary, rename downloaded files to `your-workflow-slug-classifications.csv` (e.g. `wi-milwaukee-county-classifications.csv`) and `your-workflow-slug-workflows.csv` (e.g. `wi-milwaukee-county-workflows.csv`)
1. Process exported batch results from Zooniverse (Using command line tools)
```
python manage.py generate_zooniverse_export --workflow "WI Milwaukee County"
```
1. Load raw and aggregated Zooniverse responses into individual property matches
```
python manage.py load_zooniverse_export --slow --workflow "WI Milwaukee County"
```
1. Join deed images to zooniverse subjects
```
python manage.py join_deeds_to_subjects --workflow "WI Milwaukee County"
```
1. Re-join manual corrections to subjects
```
python manage.py connect_manual_corrections --workflow "WI Milwaukee County"
python manage.py connect_extra_parcels --workflow "WI Milwaukee County"
```
1. Automated join of matches to modern parcel map
```
python manage.py rebuild_covenant_spatial_lookups --workflow "WI Milwaukee County"
python manage.py match_parcels --workflow "WI Milwaukee County"
```
1. Manual cleanup as needed.
1. Export shapefile/data layers
```
python manage.py dump_covenants_shapefile --workflow "WI Milwaukee County"
python manage.py dump_covenants_geojson --workflow "WI Milwaukee County"
python manage.py dump_covenants_csv --workflow "WI Milwaukee County"
```


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
1. Upload deed images to private s3 bucket. This will trigger lambdas to OCR the text, generate basic document statistics, check for racial terms and to make web versions of the document images.
```
python manage.py upload_deed_images --workflow "WI Milwaukee County"

 # To go back and re-OCR records that had errors:
python manage.py trigger_ocr_cleanup --workflow "WI Milwaukee County"

 # To re-do the search terms and image optimization steps, while skipping OCR:
python manage.py trigger_lambda_refresh --workflow "WI Milwaukee County"

 # To delete:
python manage.py delete_raw_images
```
1. Gather results of document image uploads into the Django app. Optionally, add supplemental info like missing doc nums that have been provided in a separate csv.
```
python manage.py gather_deed_images --workflow "WI Milwaukee County"
```
1. Gather list of positive matches for racially restrictive language and join to deed image records in Django app
```
python manage.py gather_image_hits --workflow "WI Milwaukee County"
```
1. Upload batch of records to Zooniverse for community confirmation
```
python manage.py upload_to_zooniverse --workflow "WI Milwaukee County" -n 200
```
1. (Or, optionally) Export manifest in order to upload matching files to Zooniverse (or point to S3 images)
```
python manage.py build_zooniverse_manifest --workflow "WI Milwaukee County"
```
1. Process exported batch results from Zooniverse (Using command line tools)
```
python manage.py generate_zooniverse_export --workflow "WI Milwaukee County"
```
1. Load raw and aggregated Zooniverse responses into individual property matches
```
python manage.py load_zooniverse_export --slow --workflow "WI Milwaukee County"
```
1. Join deed images to zooniverse subjects
```
python manage.py join_deeds_to_subjects --workflow "WI Milwaukee County"
```
1. Optional: Load images to s3 and/or list of plats/additions to help with autojoin to Parcels and with manual research
```
python manage.py upload_plat_images --workflow "WI Milwaukee County"
python manage.py load_plat_records --workflow "WI Milwaukee County"
```
1. Optional: Load subdivision spatial layer to help with autojoin to Parcels and with manual research
```
python manage.py load_subdivision_shp --workflow "WI Milwaukee County"
```
1. Load modern parcel shapefiles with unique fields mapped to unified subset
```
python manage.py load_parcel_shp --workflow "WI Milwaukee County"
```
1. Automated join of matches to modern parcel map
```
python manage.py rebuild_parcel_spatial_lookups --workflow "WI Milwaukee County"
python manage.py rebuild_covenant_spatial_lookups --workflow "WI Milwaukee County"
python manage.py match_parcels --workflow "WI Milwaukee County"
```
1. Export list of unmatched confirmed covenants
1. Manual (GUIish?) cleanup of bad joins, split parcels, etc.
1. Metes and bounds manual tracing
1. Final shapefile/data layers
```
python manage.py dump_covenants_shapefile --workflow "WI Milwaukee County"
python manage.py dump_covenants_geojson --workflow "WI Milwaukee County"
python manage.py dump_covenants_csv --workflow "WI Milwaukee County"
```

## Other workflow elements
Manual corrections, extra parcel records and alternate names for plats are stored as separate models from the ZooniverseSubject, Plat or Subdivision models so edits are non-destructive and can be recreated in case of a need to re-import from Zooniverse (or plat maps or Subdivision shapefiles), or can be rolled back as new information emerges.
```
# To archive manual entries in a CSV for later re-import:
python manage.py dump_manual_corrections --workflow "WI Milwaukee County"
python manage.py dump_extra_parcels --workflow "WI Milwaukee County"

# To re-import a those manual entries from csv export:
python manage.py load_manual_corrections --workflow "WI Milwaukee County" --infile relative/path/to/file
python manage.py load_extra_parcels --workflow "WI Milwaukee County" --infile relative/path/to/file

# To manually re-join corrections to subjects
python manage.py connect_manual_corrections --workflow "WI Milwaukee County"
python manage.py connect_extra_parcels --workflow "WI Milwaukee County"

# Same as above, but only needed if you re-import your subdivision spatial or plat data)
python manage.py dump_plat_alternate_names --workflow "WI Milwaukee County"
python manage.py dump_subdivision_alternate_names --workflow "WI Milwaukee County"

python manage.py load_plat_alternate_names --workflow "WI Milwaukee County" --infile relative/path/to/file
python manage.py load_subdivision_alternate_names --workflow "WI Milwaukee County" --infile relative/path/to/file

# To manually re-join corrections to subdivisions/plats (mostly you will never run these, which are run as a part of the previous "load" scripts)
python manage.py connect_plat_alternate_names --workflow "WI Milwaukee County"
python manage.py connect_subdivision_alternate_names --workflow "WI Milwaukee County"
```

## Standalone deed uploader
Often deed images are stored on a local machine or network drive, and it's not feasible or efficient to move them. This standalone uploader is designed to avoid the user having to do a full install on this computer.

- [mp-upload-deed-images-standalone](https://github.com/UMNLibraries/mp-upload-deed-images-standalone)

## Lambda functions used for OCR step machine
The individual lambda functions that make up the OCR, term search and web image optimization processes are in separate repositories:
- [mp-covenants-split-pages](https://github.com/UMNLibraries/mp-covenants-split-pages)
- [mp-covenants-ocr-page](https://github.com/UMNLibraries/mp-covenants-ocr-page)
- [mp-covenants-term-search-basic](https://github.com/UMNLibraries/mp-covenants-term-search-basic)
- [mp-covenants-resize-image](https://github.com/UMNLibraries/mp-covenants-resize-image)
- [mp-covenants-fake-ocr](https://github.com/UMNLibraries/mp-covenants-fake-ocr)

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
