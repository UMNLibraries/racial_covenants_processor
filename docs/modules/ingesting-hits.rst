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

3. (Optional) Exempt some hits from upload to Zooniverse as needed by providing a CSV file with a unique lookup value (default is the `s3_lookup` field). By default, `bool_match` will be set to False, with `bool_exception` and `bool_manual` set to True. However, by passing the `--preserve-match` flag, `bool_match` will still be set to True. This will still prevent these pages from being uploaded to Zooniverse.

.. code-block:: bash

    python manage.py set_manual_exceptions --workflow "WI Milwaukee County"