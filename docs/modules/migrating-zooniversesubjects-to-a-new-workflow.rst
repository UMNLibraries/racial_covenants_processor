Migrating ZooniverseSubjects to a new workflow
==============================================

This procedure is designed to mitigate the situation we faced in Ramsey County, where previous work in a different version of the Mapping Prejudice workflow needed to be integrated with an updated process with more data. The goals are:
- Don't ask community mapmaking volunteers to waste time re-classifying pages we previously looked at
- Have both old and new completed covenants exported from a single workflow to avoid having to reconcile them repeatedly
- Have migrated ZooniverseSubjects linked to DeedPage records in the NEW workflow

1. Ensure the new destination workflow exists

2. Export ZooniverseSubject and related model data from the old workflow

.. code-block:: bash

    python manage.py dump_django_zooniversesubjects --workflow "Ramsey County"
    python manage.py dump_django_individual_responses --workflow "Ramsey County"
    python manage.py dump_manual_corrections --workflow "Ramsey County"
    python manage.py dump_extra_parcels --workflow "Ramsey County"
    python manage.py dump_manual_pin_links --workflow "Ramsey County"

3. Modify the exported ZooniverseSubject CSV to change the workflow name and link to new images. We used a Jupyter notebook to update the ``workflow_name``, ``image_ids``, and ``image_links`` fields. Export to a new CSV.

4. Load the exports to the new workflow in this order, which will also connect the supporting models to the ZooniverseSubjects.

.. code-block:: bash

    python manage.py load_django_zooniversesubjects --workflow "MN Ramsey County" --infile path/to/csv.csv
    python manage.py load_django_individual_responses --workflow "MN Ramsey County" --infile path/to/csv.csv
    python manage.py load_manual_corrections --workflow "MN Ramsey County" --infile path/to/csv.csv
    python manage.py load_extra_parcels --workflow "MN Ramsey County" --infile path/to/csv.csv
    python manage.py load_manual_pin_links --workflow "MN Ramsey County" --infile path/to/csv.csv

5. Re-do join of matches to modern parcel map

.. code-block:: bash
    
    python manage.py rebuild_covenant_spatial_lookups --workflow "MN Ramsey County"
    python manage.py match_parcels --workflow "MN Ramsey County"

This process will need to be repeated if new ZooniverseSubjects are loaded from newly retired Zooniverse work