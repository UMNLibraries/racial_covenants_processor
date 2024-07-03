.. _ingesting-hits:

Ingesting results of initial processing
=======================================

After uploading of images and initial processing is complete, it's time to ingest the results into the Deed Machine's Django component.

Before ingestion, be sure to create a regular expression for filepath data extraction and any needed supplemental info as outlined in :ref:`starting-a-workflow`.

1. Gather results of document image uploads into the Django app. Optionally, add supplemental info like missing doc nums that have been provided in a separate csv.

.. code-block:: bash

    python manage.py gather_deed_images --workflow "WI Milwaukee County"


2. Gather list of positive matches for racially restrictive language and join to deed image records in Django app

.. code-block:: bash

    python manage.py gather_image_hits --workflow "WI Milwaukee County"