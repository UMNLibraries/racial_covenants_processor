Downloading new batches of Zooniverse results
=============================================

1. Export updated manual corrections in case something goes wrong, though you generally won't need to reload these (just re-join) unless your database needs to be completely rebuilt

.. code-block:: bash

    python manage.py dump_manual_corrections --workflow "WI Milwaukee County"
    python manage.py dump_extra_parcels --workflow "WI Milwaukee County"
    python manage.py dump_manual_pin_links --workflow "WI Milwaukee County"

2. Create and download a fresh Zooniverse export from the Zooniverse Lab tab.  
    A. Click Lab > Data Exports > Request new workflow classification export  
    B. Click Lab > Data Exports > Request new workflow export  
    C. Download files once notified by email.  
    D. Place downloaded files in a folder named the workflow slugs. (I retain old versions of this folder by renaming with a date stamp, e.g. your-workflow-slug-20240401):

    ::

        racial_covenants_processor
        ├── racial_covenants_processor
            ├── data
                ├── zooniverse_exports
                    |── your-workflow-slug/
                        |── your-workflow-slug-classifications.csv
                        |── your-workflow-slug-workflows.csv

    E. If necessary, rename downloaded files to ``your-workflow-slug-classifications.csv`` (e.g. ``wi-milwaukee-county-classifications.csv``) and ``your-workflow-slug-workflows.csv`` (e.g. ``wi-milwaukee-county-workflows.csv``)

3. Process exported batch results from Zooniverse (Using command line tools)

.. code-block:: bash
  
    python manage.py generate_zooniverse_export --workflow "WI Milwaukee County"

4. Load raw and aggregated Zooniverse responses into individual property matches

.. code-block:: bash
    
    python manage.py load_zooniverse_export --slow --workflow "WI Milwaukee County"

5. (Optional) Load ZooniverseSubject objects migrated from another workflow. (See :ref:`migrating-zooniversesubjects-to-a-new-workflow`.) Do this each time working with a migrated workflow with new Zooniverse results.

.. code-block:: bash

    python manage.py load_django_zooniversesubjects --workflow "WI Milwaukee County" --infile path/to/csv.csv

6. Join deed images to zooniverse subjects

.. code-block:: bash
    
    python manage.py join_deeds_to_subjects --workflow "WI Milwaukee County"

7. Re-join manual corrections to subjects

.. code-block:: bash
    
    python manage.py connect_manual_corrections --workflow "WI Milwaukee County"
    python manage.py connect_extra_parcels --workflow "WI Milwaukee County"
    python manage.py connect_manual_pin_links --workflow "WI Milwaukee County"

8. Automated join of matches to modern parcel map

.. code-block:: bash
    
    python manage.py rebuild_covenant_spatial_lookups --workflow "WI Milwaukee County"
    python manage.py match_parcels --workflow "WI Milwaukee County"

9. :doc:`Manual cleanup <manual-data-cleaning>` of non-mapped covenants as needed.

10. Export shapefile/data layers

.. code-block:: bash

    python manage.py dump_covenants_shapefile --workflow "WI Milwaukee County"
    python manage.py dump_covenants_geojson --workflow "WI Milwaukee County"
    python manage.py dump_covenants_csv --workflow "WI Milwaukee County"

11. These exports are slightly different. Each row in these exports represents a covenanted document, not a modern parcel. These may be useful for covenants discharge or for identifying covenants that could not (so far) be mapped. They are not used for our count of racial covenants.

.. code-block:: bash
    python manage.py dump_unmapped_csv --workflow "WI Milwaukee County"
    python manage.py dump_all_covenanted_docs_csv --workflow "WI Milwaukee County"

