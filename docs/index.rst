.. The Deed Machine documentation master file, created by
   sphinx-quickstart on Fri Jun 14 13:08:44 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The Deed Machine
============================================

The Deed Machine is a multi-language set of tools that use OCR and crowdsourced transcription to identify racially restrictive covenant language, then map the results.

The Deed Machine was created at Mapping Prejudice at the University of Minnesota Libraries. Current collaborators include Michael Corey, Suleman Diwan, Justin Schell, and the University of Minnesota Libraries IT staff.

.. image:: https://s3.us-east-2.amazonaws.com/static.mappingprejudice.com/deed-machine/Draft%20-%20Updated%20Workflow_alpha.png
  :width: 800
  :alt: A diagram of the components of the Deed Machine. To the left, an initial processing stage using AWS Step Functions is used to output a series of S3 files, which are ingested into a Django project in the center of the diagram.

.. toctree::
   :maxdepth: 2
   :caption: Common workflows

   modules/downloading-new-results.rst
   modules/manual-data-cleaning.rst

.. toctree::
   :maxdepth: 2
   :caption: Models

   modules/apps-deed-models.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
