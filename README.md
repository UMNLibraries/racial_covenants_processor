# The Deed Machine

The Deed Machine is a multi-language set of tools that use OCR and crowdsourced transcription to identify racially restrictive covenant language, then map the results.

Racial covenants are clauses that were inserted into property deeds to prevent people who are not white from buying or occupying land. As of June 2024, Mapping Prejudice volunteers have helped to map [more than 52,000 covenanted properties](https://github.com/umnlibraries/mp-us-racial-covenants) across 3 states, with more on the way soon.

The Deed Machine was created at [Mapping Prejudice](https://mappingprejudice.umn.edu/) at the [University of Minnesota Libraries](https://www.lib.umn.edu/). Current collaborators include Michael Corey, Suleman Diwan, Justin Schell, and the University of Minnesota Libraries IT staff.

This is the code repository for the Django component of the Deed Machine, `racial_covenants_processor`. See [the full docs](https://the-deed-machine.readthedocs.io/en/latest/) for more information about other components.

<img src="https://s3.us-east-2.amazonaws.com/static.mappingprejudice.com/deed-machine/Draft%20-%20Updated%20Workflow_alpha.png"/>


## Key links
- [License](https://github.com/UMNLibraries/racial_covenants_processor/blob/main/LICENSE)
- [Documentation](https://the-deed-machine.readthedocs.io/en/latest/)
- [Downloadable Racial covenants data](https://github.com/umnlibraries/mp-us-racial-covenants)
- [Mapping Prejudice main site](https://mappingprejudice.umn.edu/)

## Software requirements
- geos and gdal
- proj
- pandas and geopandas
- pipenv
- PostGIS/PostgreSQL
- AWS SAM for lambdas (separate repos)
- libmagic (mostly to silence panoptes/zooniverse warnings)

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

Testing a change