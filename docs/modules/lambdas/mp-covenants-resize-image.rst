.. _mp-covenants-resize-image:

mp-covenants-resize-image
===============================

- Code: `mp-covenants-resize-image on Github <https://github.com/UMNLibraries/mp-covenants-resize-image>`_

This component receives a TIF or JPEG file and creates a scaled-down, web-friendly JPEG with a watermark on it for public transcription using the Pillow library. The output filename includes a randomized UUID suffix to deter scraping, since this image's permissions will be set to publicly viewable. This is the final Lambda in the Deed Machine initial processing Step Function.


Steps of the function
---------------------

1. Check event for valid image.
2. Resize image to below 1 MB (Zooniverse requirement), if necessary, and convert to JPEG, if necessary.
3. Add watermark.
4. Return path to final image.

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
