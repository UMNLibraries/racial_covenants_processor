.. _mp-covenants-fake-ocr:

mp-covenants-fake-ocr
===============================

- Code: `mp-covenants-fake-ocr on Github <https://github.com/UMNLibraries/mp-covenants-fake-ocr>`_

This component is designed to mimic actions of OCR step, but skip actual OCR, to avoid needing to re-OCR files that have already been OCRed, which is relatively expensive. The function opens a previously created OCR JSON saved to s3 and passes data about it on to the next step. This lambda is only used for DeedPageProcessorFAKEOCR, which is run to correct errors in post-OCR stages of the main DeedPageProcessor Step Function. This step function is triggered by the Django management command `trigger_lambda_refresh`


Steps of the function
---------------------

1. Check event for valid raw image path.
2. Determine matching OCR JSON and OCR TXT s3 paths, which should already exist
3. Open pre-existing OCR JSON file
4. Generate new UUID and stats, save stats object
5. Pass output on to next stage.

Software development requirements
---------------------------------

The Lambda components of the Deed Machine are built using Amazon's Serverless Application Model (SAM) and the AWS SAM CLI tool.

- Pipenv (Can use other virtual environments, but will require fiddling on your part)
- AWS SAM CLI
- Docker
- Python 3

Quickstart commands
-------------------

To build the application:

.. code-block:: bash

    pipenv install
    pipenv shell
    sam build

To rebuild and deploy the application:

.. code-block:: bash

    sam build && sam deploy

To run tests:

.. code-block:: bash

    pytest
