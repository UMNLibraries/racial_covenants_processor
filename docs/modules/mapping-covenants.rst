.. _mapping-covenants:

Mapping covenants
========================================

Rebuilding spatial lookups
--------------------------

.. code-block:: bash

    python manage.py rebuild_parcel_spatial_lookups --workflow "WI Milwaukee County"
    python manage.py rebuild_covenant_spatial_lookups --workflow "WI Milwaukee County"

Automated join of matches to modern parcel map
----------------------------------------------

.. code-block:: bash

    python manage.py match_parcels --workflow "WI Milwaukee County"
    