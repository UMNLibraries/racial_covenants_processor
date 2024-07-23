.. _mp-covenants-split-pages:

mp-covenants-split-pages
========================

- Code: `mp-covenants-split-pages on Github <https://github.com/UMNLibraries/mp-covenants-split-pages>`_

This component receives information about a newly uploaded or updated image, generally via an event triggered by a matching S3 upload event. This is the first Lambda in the Deed Machine initial processing Step Function. The function examines the image to determine what, if any, reprocessing operations are necessary before the image can be fully processed by the Deed Machine. If processing is needed, a new version of the image will either overwrite the original file in S3, or create a `_SPLITPAGE_` file if the original file is a multipage TIF.

Any modications requiring overwrite or new image generation will trigger a new invocation of the step function. Once an image can pass through this Lambda without modification, it is passed on to the next step of the step function.

Steps of the function
---------------------

1. Check event for valid image. Ignore if .DS_Store.
2. Find number of pages in file (i.e. multipage TIF)
3. If more than one page present, create a copy of page using Pillow and append _SPLITPAGE_ with appropriate page number. 
4. Check for a compatible image mode (RGB is good, indexed is bad). Resave in RGB if bad.
5. Check for oversized image dimensions. Max dimensions for Textract are 10,000 pixels in either dimension.
6. Check for oversized image memory. Textract has a limit of 10485760 bytes. We round down by 1% to make up for decode differences.
7. If image has been modified or more than one page present, save updated version(s) and exit.
8. If image unmodified after passing through all steps, add to "pages" output object, which is passed to next stage of step function.


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
