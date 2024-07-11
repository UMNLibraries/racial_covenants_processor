# Racial Covenants Processor

This is the main repository for The Deed Machine, a generalized set of tools to OCR property deeds to look for racially restrictive covenant language, then map the results.

The Deed Machine was created at Mapping Prejudice at the University of Minnesota Libraries. Current collaborators include Michael Corey, Justin Schell and Nicholas Boren.

<img src="https://s3.us-east-2.amazonaws.com/static.mappingprejudice.com/deed-machine/Draft%20-%20Updated%20Workflow_alpha.png"/>


## Software requirements
- geos and gdal
- proj
- pandas and geopandas
- pipenv
- PostGIS/PostgreSQL
- AWS SAM for lambdas (separate repos)
- libmagic (mostly to silence panoptes/zooniverse warnings)

## Documentation

- Full documentation, still a work in progress: https://the-deed-machine.readthedocs.io/en/latest/ 


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

### 6. For deedstats notebook (not yet committed)
```python manage.py shell_plus --notebook```
