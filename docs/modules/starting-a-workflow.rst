.. _starting-a-workflow:

Starting a workflow
===================

In the Deed Machine, each county or other jurisdiction that provides sets of records to be analyzed is represented as a ZooniverWorkflow, or workflow for short.

1. For each new workflow, start by adding an entry in the Python config dictionary object in ``local_settings.py``. ``local_settings.py`` is ignored by git, so if you have not previously made a ``local_settings.py`` file, do so now, saved to the ``racial_covenants_processor/settings/`` folder. This file is imported at the end of the main settings file, common.py (which should generally not be edited by end users), and settings placed in ``local_settings.py`` will override those settings.

.. code-block:: python

    ZOONIVERSE_QUESTION_LOOKUP = {
        'WI Milwauke County': {
        },
        'MN Olmsted County': {
        ...
        }
    }

2. The folder structure and filenames of the records provided by records custodians can provide necessary and bonus information about each record. For example, folders and filenames can include the document date (``doc_date``), document number (``doc_num``) book and page (``book_id`` and ``page_num``). For each county, you will need to write a regular expression to parse the folder and filenames after they have been uploaded to S3 during the initial processing phase. While it is not strictly necessary to write this regular expression before file upload, it is a good practice to think through whether the folder structure and filenames as delivered will be able to be successfully generalized into a regular expression in order to avoid the need for either exceptionally complex regular expressions or costly re-uploads.

The best way to build your regular expression is to experiment at Pythex.org with sample paths from the ``s3_path`` field of the CSV files produced by the standalone uploader, which are stored in the ``data`` folder of wherever you have installed the `mp-upload-deed-images-standalone <https://github.com/UMNLibraries/mp-upload-deed-images-standalone>`_ application.

For example, during the process of ingesting results from S3 into the Deed Machine's database, the following regular expression captures data including the workflow slug, as well as the ``doc_type``, ``batch_id``, ``book_id``, ``doc_num``, and ``split_page_num`` fields that will be saved to the database.

.. code-block:: python

    ZOONIVERSE_QUESTION_LOOKUP = {
        'WI Milwauke County': {
            ...
        },
        'MN Olmsted County': {
            'deed_image_regex': r'/(?P<workflow_slug>[A-z\-]+)/OlmstedCounty(?P<doc_type>[A-Za-z]+)/(?P<batch_id>[A-Za-z]+)/?(?P<book_id>[A-Za-z\-\d]+)?/(?P<doc_num>[A-Z\d\.]+)(?:_SPLITPAGE_)?(?P<split_page_num>(?<=_SPLITPAGE_)\d+)?',
        }
    }

In order to facilitate correct pagination, for each image you will need to capture, at minimum:

- Either a ``doc_num``, or both a ``book_id`` and ``page_num``
- The ``split_page_num`` generated by the initial processing stage when mult-page TIF files are processed. Note that while SPLITPAGE will not show up in the list of s3_paths in the CSVs generated by the `mp-upload-deed-images-standalone <https://github.com/UMNLibraries/mp-upload-deed-images-standalone>`_ application, they still should be accounted for in your regular expression. This means that regular expressions will almost always need to end with ``(?:_SPLITPAGE_)?(?P<split_page_num>(?<=_SPLITPAGE_)\d+)?``, as shown below.

4. (Optional) If the required ``doc_num`` or ``book_id``\/``page_num`` combination are not parseable from the folder/filenames, then a suppliemental CSV should be included at the time of ingestion after initial processing. This CSV will allow the Deed Machine to link additional information to each image by using a lookup table based on metadata pulled from the images folder and pathname.

To add data from one or more supplemental CSV files, add a ``deed_supplemental_info`` list to the ``ZOONIVERSE_QUESTION_LOOKUP`` config object:

.. code-block:: python

    ZOONIVERSE_QUESTION_LOOKUP = {
        'WI Milwauke County': {
            ...
        },
        'MN Olmsted County': {
            'deed_image_regex': r'/(?P<workflow_slug>[A-z\-]+)/OlmstedCounty(?P<doc_type>[A-Za-z]+)/(?P<batch_id>[A-Za-z]+)/?(?P<book_id>[A-Za-z\-\d]+)?/(?P<doc_num>[A-Z\d\.]+)(?:_SPLITPAGE_)?(?P<split_page_num>(?<=_SPLITPAGE_)\d+)?',
            'deed_supplemental_info': [
                {
                    'data_csv': '/Users/mcorey/Documents/Deed projects/mn/ramsey/ramsey_recorder_supplemental_info/Abstract_20191106_header.csv',  # Absolute path to supplemental CSV
                    'join_field_deed': 'doc_alt_id',  # Join field drawn from imported image path
                    'join_field_supp': 'itemnum',  # Join field in supplemental CSV
                    'mapping': {
                        'doc_num': 'mp_doc_num', # deed machine varname: CSV column name
                        'doc_type': 'landtype' # deed machine varname: CSV column name
                    }
                }
            ],
        }
    }

In the example above, the ingestion process will expect each ingested file to include a ``doc_alt_id`` field in the regular expression that matches the value ``itemnum`` in the supplemental spreadsheet. Based on the values in the ``mapping`` section of the ``deed_supplemental_info`` dictionary, the values in the CSV's ``mp_doc_num`` column will be ingested into the Deed Machine's ``doc_num`` field, and likewise values in the ``landtype`` CSV field will be ingested into the Deed Machine's ``doc_type`` field.

.. list-table:: Sample supplemental CSV with matching data
    :header-rows: 1

    * - itemnum
      - pagecnt
      - itemname
      - docnum
      - landtype
      - instrumenttype
      - mp_doc_num
    * - 12117219
      - 1
      - ABSTRACT - 1483219 -  - R-CONVERSION
      - 1483219
      - ABSTRACT
      - R-CONVERSION
      - A1483219
    * - 12117223
      - 1
      - ABSTRACT - 1483678 -  - R-CONVERSION
      - 1483678
      - ABSTRACT
      - R-CONVERSION
      - A1483678
    * - 12117224
      - 1
      - ABSTRACT - 1483679 -  - R-CONVERSION
      - 1483679
      - ABSTRACT
      - R-CONVERSION
      - A1483679
    * - 12117228
      - 1
      - ABSTRACT - 1485353 -  - R-CONVERSION
      - 1485353
      - ABSTRACT
      - R-CONVERSION
      - A1485353


3. Create a Django ZooniverseWorkflow object

.. code-block:: bash

    python manage.py create_workflow --workflow "WI Olmsted County"
