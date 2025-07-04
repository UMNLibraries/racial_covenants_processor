The Deed Machine
================

.. image:: https://s3.us-east-2.amazonaws.com/static.mappingprejudice.com/deed-machine/MappingPrejudice_C_600.png
   :width: 200
   :align: right
   :alt: Mapping Prejudice logo
   :target: https://mappingprejudice.umn.edu/

`The Deed Machine <https://github.com/umnlibraries/racial_covenants_processor>`_ is a multi-language set of tools that use OCR and crowdsourced transcription to identify racially restrictive covenant language, then map the results.

Racial covenants are clauses that were inserted into property deeds to prevent people who are not white from buying or occupying land. As of June 2024, Mapping Prejudice volunteers have helped to map `more than 52,000 covenanted properties <https://github.com/umnlibraries/mp-us-racial-covenants>`_ across 3 states, with more on the way soon.

The Deed Machine was created at `Mapping Prejudice <https://mappingprejudice.umn.edu/>`_ at the `University of Minnesota Libraries <https://www.lib.umn.edu/>`_. Current collaborators include Michael Corey, Suleman Diwan, Justin Schell, and the University of Minnesota Libraries IT staff.

.. image:: _static/DeedMachineBasicSteps2023.png
  :width: 800
  :alt: A diagram showing the five basic steps of the Deed Machine process: Digitized Docs, Optical Character Recognition, Text, Zooniverse, and Digitized map.

Deed Machine full workflow
--------------------------

.. image:: https://s3.us-east-2.amazonaws.com/static.mappingprejudice.com/deed-machine/Draft%20-%20Updated%20Workflow_alpha.png
  :width: 800
  :alt: A diagram of the components of the Deed Machine. To the left, an initial processing stage using AWS Step Functions is used to output a series of S3 files, which are ingested into a Django project in the center of the diagram.

.. toctree::
   :maxdepth: 2
   :caption: The Deed Machine

   modules/funding.rst
   modules/requirements.rst
   modules/components.rst
   modules/installation.rst
   modules/development.rst
   modules/support.rst
   modules/license.rst

.. toctree::
   :maxdepth: 2
   :caption: Common workflows

   modules/starting-a-workflow.rst
   modules/uploading-files.rst
   modules/ingesting-hits.rst
   modules/uploading-to-zooniverse.rst
   modules/uploading-parcel-data.rst
   modules/downloading-new-results.rst
   modules/mapping-covenants.rst
   modules/manual-data-cleaning.rst
   modules/migrating-zooniversesubjects-to-a-new-workflow.rst

.. toctree::
   :maxdepth: 2
   :caption: Django models

   modules/django-models.rst
   modules/apps-deed-models.rst
   modules/apps-parcel-models.rst
   modules/apps-plat-models.rst
   modules/apps-zoon-models.rst
   
.. toctree::
   :maxdepth: 2
   :caption: Step function lambdas

   modules/lambdas/mp-covenants-split-pages.rst
   modules/lambdas/mp-covenants-ocr-page.rst
   modules/lambdas/mp-covenants-term-search-basic.rst
   modules/lambdas/mp-covenants-resize-image.rst
   modules/lambdas/mp-covenants-fake-ocr.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
