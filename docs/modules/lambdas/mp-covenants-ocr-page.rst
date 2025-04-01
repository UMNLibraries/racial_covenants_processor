.. _mp-covenants-ocr-page:

mp-covenants-ocr-page
========================

- Code: `mp-covenants-ocr-page on Github <https://github.com/UMNLibraries/mp-covenants-ocr-page>`_

This component receives a link to an s3 image key and runs Textract's detect_document_text method to create creates 3 new files: a Textract JSON file, a simple TXT file containing a text blob of all text found, and a stats json, which contains basic statistics like the amount of the page that is estimated to be handwritten, the number of lines, and number of words. Output of this function is sent to a parallel step that will use the OCRed text to search for racial covenant terms, and another that will create a web-friendly version of the image. This is the second Lambda in the Deed Machine initial processing Step Function.


Steps of the function
---------------------

1. Check event for valid image.
2. If the image key includes _SPLITPAGE_, wait for 0.3 seconds times the page number to avoid overloading Textract.
3. Run Textract's detect_document_text method
4. From Textract results, extract lines and words
5. Calculate handwritten percentage
6. Generate unique UUID to be applied to web-friendly image in next step
7. Save JSON, TXT and Stat files to S3
8. Pass list of files generated and handwritten percentage to next step.

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


Example with non-default aws profile:

.. code-block:: bash
    sam build && sam deploy --profile contracosta --config-env contracosta

To run tests:

.. code-block:: bash

    pytest
