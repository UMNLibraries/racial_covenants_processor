Uploading images/initial processing
===================================

Option 1: Upload from local installation
----------------------------------------

If the property images to be processed are stored on a drive attached to the same computer where the Deed Machine is installed locally, then the ``upload_deed_images`` command can be run directly from the local installation.

.. code-block:: bash

    python manage.py upload_deed_images --workflow "WI Milwaukee County"

To use this option, the XXXX values must be added to the ``ZOONIVERSE_QUESTION_LOOKUP`` workflow config lookup for this workflow in ``local_settings.py``.


Option 2: Upload with the standalone Deed Machine uploader
----------------------------------------------------------

(Recommended for large sets of images)

Often deed images are stored on a local machine or network drive, and it's not feasible or efficient to move them. This standalone uploader is designed to avoid the user having to do a full install on this computer, which is particularly useful when moving millions of files may be time-consuming or present storage issues.

- `mp-upload-deed-images-standalone <https://github.com/UMNLibraries/mp-upload-deed-images-standalone>`_


Related commands
----------------

To go back and re-OCR records that had errors:

.. code-block:: bash
    python manage.py trigger_ocr_cleanup --workflow "WI Milwaukee County"

To re-do the search terms and image optimization steps, while skipping most costly OCR step:

.. code-block:: bash
    python manage.py trigger_lambda_refresh --workflow "WI Milwaukee County"

To delete image files from S3 (Warning: cannot be undone):

.. code-block:: bash
    python manage.py delete_raw_images --workflow "Your workflow here"