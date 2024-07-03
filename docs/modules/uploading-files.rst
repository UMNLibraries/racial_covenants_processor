Uploading images/initial processing
===================================

Option 1: Upload from local installation
----------------------------------------

If the property images to be processed are stored on a drive attached to the same computer where the Deed Machine is installed locally, then the ``upload_deed_images`` command can be run directly from the local installation.

.. code-block:: bash

    python manage.py upload_deed_images --workflow "WI Milwaukee County"

To use this option, the ``deed_image_glob_root`` and ``deed_image_glob_remainders`` values must be added to the ``ZOONIVERSE_QUESTION_LOOKUP`` workflow config lookup for this workflow in ``local_settings.py`` (see `mp-upload-deed-images-standalone <https://github.com/UMNLibraries/mp-upload-deed-images-standalone>`_) for more details.


Option 2: Upload with the standalone Deed Machine uploader
----------------------------------------------------------
(Recommended for large sets of images)

Often deed images are stored on a local machine or network drive, and it's not feasible or efficient to move them. This standalone uploader is designed to avoid the user having to do a full install on this computer, which is particularly useful when moving millions of files may be time-consuming or present storage issues.

- `mp-upload-deed-images-standalone <https://github.com/UMNLibraries/mp-upload-deed-images-standalone>`_

1. On the computer where images are stored (or where an external drive with images is connected), install the standalone uploader by cloning the Github repository. Your local Github settings and Python environment (e.g. conda or pipenv) may require different steps.

.. code-block:: bash

    git clone https://github.com/UMNLibraries/mp-upload-deed-images-standalone.git  # Assumes https authentication
    cd mp-upload-deed-images-standalone.git
    pip install -r requirements.txt

2. Make a copy of the ``config.py.sample`` file called ``config.py``. The resulting config file is ignored by git, so be sure to make a backup copy of your local configuration for your reference.

3. Edit the ``WORKFLOW_SETTINGS`` object in ``config.py`` to tell the program where to find your raw images for upload. Replace the values to match your AWS keys and S3 bucket name.

.. code-block:: python

    AWS_ACCESS_KEY_ID = 'my-access-key'
    AWS_SECRET_ACCESS_KEY = 'my-secret-key'
    AWS_STORAGE_BUCKET_NAME = 'my-bucket-name'

    WORKFLOW_SETTINGS = {
        'WI Milwaukee County': {
            'deed_image_glob_root': '/abs/path/to/image/root/',
            'deed_image_glob_remainders': ['**/*.tif', '**/*.jpg'],  # A list of possible paths/extensions from root to check
        }
    }

The program uses glob to locate files, so see glob documentation for details on how to match or ignore different patterns. For example, the settings above will match and files with the .tif or .jpg extension (note that these are case-sensitive) in any subfolder below ``/abs/path/to/image/root/``. As written, it would not match a file with a ``.TIF`` or ``.tiff`` extension, for example, so before upload be sure to examine your local cache of images to be sure you understand the folder and file variations. Before upload, it's a good idea to look at these variations to determine if you will be able to write a single regular expresion to parse the folders and filenames in order to extract valuable metadata like document number, doc type, or date after upload. (See :ref:`starting-a-workflow` for more details.) While experienced regular expressions users can accomodate a fair amount of complexity, if there is too much variation in folder structure or filenames in a county's records, it might be worth programmatically re-arranging or renaming files before upload. This is outside the scope of the Deed Machine documentation, however.

4. Decide how many threads and what mintime value to set, and start your upload.

The basic upload command is:

.. code-block:: bash

    python upload.py --workflow "Your workflow name"

The standalone uploader uses Python multithreading to maximize speed, and by default, will upload files as fast as it can with no delays, using 8 threads. If your network is blessed with fast-enough upload speeds, it is possible to exceed your AWS usage quotas, particularly the Textract usage quota.

You can tune your uploads by using the ``--pool`` and ``--mintime`` flags.

The ``--pool`` flag controls how many concurrent uploads to trigger. The default is 8.

The ``--mintime`` flag controls how much of a delay to add, if necessary, after each upload to prevent quota overages. For example, setting a ``--minetime`` of 0.5 indicates that if an indvidual upload takes less than 0.5 seconds, the thread should pause until 0.5 seconds has elapsed since starting.

The two flags can be used together:

.. code-block:: bash

    python upload.py --workflow "WI Milwaukee County" --pool 16 --mintime 0.5

This configuration will trigger 16 concurrent upload threads, each of which will be throttled to take at least 0.5 seconds before starting a new thread.

The best approach is to start slower than you think you will need to, and then gradually ramp up speeds as you monitor the progress in uploads in the AWS console, since repeating the process on images that have failed may incur duplicate costs. 

Before uploading, the uploader will scan the locations specified in the config file for matching images, then save a CSV of the matches to the ``data`` folder. On subsequent runs, to avoid re-scanning the local drive, add the ``--cache`` flag to have the uploader use the previously created CSV as the basis for upload. You can also create your own custom manifest file and place it in the data folder, named {workflow_slug}_raw_images_list.csv. Take care to keep a copy in case you forget to use the ``--cache`` flag, and it gets overwritten.

The uploader will then check the s3 bucket specified in ``config.py`` to see what images have already been successfully uploaded. This check looks for successfully created OCR files that match the filename of the raw image rather than the raw image itself. On multi-page documents that the uploader has programmatically split, if one page has successfully been OCRed, the uploader will assume that all of the pages were also successful, which is not always correct. It is best to closely monitor the Step Function status logs in the AWS console to ensure that all executions are completing successfully to ensure maximum success.

If you pass the ``--dry`` flag, the script won't upload, just check how many files have already been uploaded and how many are left.


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