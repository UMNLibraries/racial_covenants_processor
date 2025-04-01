.. _mp-covenants-term-search-fuzzy:

mp-covenants-term-search-fuzzy
===============================

- Code: `mp-covenants-term-search-fuzzy on Github <https://github.com/UMNLibraries/mp-covenants-term-search-fuzzy>`_

This component looks for racial and other terms to flag as potential racial covenants. For each term in covenant_flags, check OCR JSON file received from previous step for existance of term. This version uses the Python 'regex' module as opposed to the built-in 're' module to allow for fuzzy searching to a given tolerance. Terms, fuzziness tolerance settings, and mandatory suffixes (usually spaces) are loaded from a CSV. Some of the terms are actually exceptions rather than covenant hits, and once they reach the Django stage, will be used to mark this page as exempt from consideration as being considered as a racial covenant. Common examples of exceptions include birth certificates and military discharges, which often contain racial information but are not going to contain a racial covenant. This is the fourth Lambda in the Deed Machine initial processing Step Function.


Steps of the function
---------------------

1. Check event for valid image.
2. For each term, search each line of text for term
3. If term found, add to output JSON along with which line numbers it appears in.
4. Return path to match file.

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
