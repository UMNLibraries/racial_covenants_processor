Requirements
============

The Deed Machine uses a combination of Amazon Web Services (AWS), Django, and standalone Python components.

AWS services used
-----------------

- S3
- Lambda
- Step Functions
- Textract
- RDS
- ECL/ECS
- EC2
- AWS sam (for lambda deployment)

Django software requirements
----------------------------

In addition to the Python requirements listed in the Pipfile, to run the Deed Machine's Django components locally, you will need:

- geos and gdal
- proj
- geopandas (Python, but can require persnickety configuratino)
- pyenv 
- pipenv
- PostgreSQL/PostGIS
- libmagic (mostly to silence panoptes/zooniverse warnings)

In order to deploy Django components to production, you will additionally need:

- Docker
- AWS CLI