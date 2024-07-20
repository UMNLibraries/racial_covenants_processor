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

Re-loading parcel shapefile(s)
==============================

If you need to re-load a workflow's Parcel shapefile due to a need to add data or reformat columns, be sure to export backups of any ManualParcelCandidate objects you may have created during manual cleanup

Exporting/reconnecting ManualParcelCandidate objects
---------------------------------------

Before re-loading a parcel shapefile, create a backup of ManualParcelCandidate records.

.. code-block:: bash

    python manage.py dump_manual_parcel_candidates --workflow "WI Milwaukee County"


After you have run `load_parcel_shp`, then re-connect the ManualParcelCandidate records:

.. code-block:: bash

    python manage.py connect_manual_parcel_candidates --workflow "WI Milwaukee County"

Note that the manual parcel candidates connected in bulk will not generate join strings/join candidates until the Parcel object is saved again, or until `rebuild_parcel_spatial_lookups` is run (see mapping section).


Re-building from scratch
------------------------
If you have not deleted the ManualParcelCandidate records, you don't need to do anything else. But if you are re-constructing a database where ManualParcelCandidate records have been deleted, you will need to re-load the records.

.. code-block:: bash

    python manage.py load_manual_parcel_candidates --workflow "WI Milwaukee County"

Note: This command will also run `connect_manual_parcel_candidates`, so you don't need to do it again.
