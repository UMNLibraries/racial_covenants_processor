Migrating ZooniverseSubjects to a new workflow
==============================================

This procedure is designed to mitigate the situation we faced in Ramsey County, where previous work in a different version of the Mapping Prejudice workflow needed to be integrated with an updated process with more data. The goals are:
- Don't ask community mapmaking volunteers to waste time re-classifying pages we previously looked at
- Have both old and new completed covenants exported from a single workflow to avoid having to reconcile them repeatedly
- Have migrated ZooniverseSubjects linked to DeedPage records in the NEW workflow

1. Ensure the new destination workflow exists

2. Export ZooniverseSubject and related model data from the old workflow

.. code-block:: bash

    python manage.py dump_django_zooniversesubjects --workflow "Ramsey County (old workflow)"
    python manage.py dump_django_individual_responses --workflow "Ramsey County (old workflow)"
    python manage.py dump_manual_corrections --workflow "Ramsey County (old workflow)"
    python manage.py dump_extra_parcels --workflow "Ramsey County (old workflow)"
    python manage.py dump_manual_pin_links --workflow "Ramsey County (old workflow)"

3. Modify the exported ZooniverseSubject CSV to change the workflow name and link to new images. We used a Jupyter notebook to update the ``workflow_name``, ``deedpage_s3_lookup``, ``image_ids``, and ``image_links`` fields. Export to a new CSV.

4. Load the exports to the new workflow in this order, which will also connect the supporting models to the ZooniverseSubjects.

.. code-block:: bash

    python manage.py load_django_zooniversesubjects --workflow "MN Ramsey County" --infile path/to/csv.csv
    python manage.py load_django_individual_responses --workflow "MN Ramsey County" --infile path/to/csv.csv
    python manage.py load_manual_corrections --workflow "MN Ramsey County" --infile path/to/csv.csv
    python manage.py load_extra_parcels --workflow "MN Ramsey County" --infile path/to/csv.csv
    python manage.py load_manual_pin_links --workflow "MN Ramsey County" --infile path/to/csv.csv

5. Re-join subjects to DeedPage images

.. code-block:: bash

    python manage.py join_deeds_to_subjects --workflow "MN Ramsey County"

6. Move ManualCovenants

.. code-block:: bash

    python manage.py dump_manual_covenants --workflow "Ramsey County (old workflow)"
    python manage.py load_manual_covenants --workflow "MN Ramsey County" --infile path/to/csv.csv

7. Re-do join of matches to modern parcel map

.. code-block:: bash
    
    python manage.py rebuild_covenant_spatial_lookups --workflow "MN Ramsey County"
    python manage.py match_parcels --workflow "MN Ramsey County"


Repeating process with new batches of Zooniverse results
--------------------------------------------------------

A modified version of this process will need to be repeated if new ZooniverseSubjects are loaded from newly retired Zooniverse work.

1. Complete steps 1-4 of :ref:`downloading-new-results`

2. Load the migrated subjects to the new workflow.

.. code-block:: bash

    python manage.py load_django_zooniversesubjects --workflow "MN Ramsey County" --infile path/to/csv.csv

3. Complete the remaining steps of :ref:`downloading-new-results`