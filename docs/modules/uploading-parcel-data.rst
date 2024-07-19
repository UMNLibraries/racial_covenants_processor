.. _uploading-parcel-data:

Uploading modern parcel data for mapping
========================================

TK TK TK
---------

TK.

.. code-block:: bash

    python manage.py upload_to_zooniverse --workflow "WI Milwaukee County" -n 200

Optional: Load images to s3 and/or list of plats/additions
----------------------------------------------------------
This helps with autojoin to Parcels and with manual research

.. code-block:: bash

    python manage.py upload_plat_images --workflow "WI Milwaukee County"
    python manage.py load_plat_records --workflow "WI Milwaukee County"

Optional: Load subdivision spatial layer
----------------------------------------
This helps with autojoin to Parcels and with manual research

.. code-block:: bash

    python manage.py load_subdivision_shp --workflow "WI Milwaukee County"

Load modern parcel shapefile(s)
-------------------------------
...with unique fields mapped to unified subset

.. code-block:: bash

    python manage.py load_parcel_shp --workflow "WI Milwaukee County"
