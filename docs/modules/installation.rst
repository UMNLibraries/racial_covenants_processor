Installation
============

Django installation process
---------------------------

These steps assume you already have `the repo<https://github.com/UMNLibraries/racial_covenants_processor/tree/main>`__ cloned and the following installed:
* Python 3.12
* pipenv
* gdal
* PostgreSQL
* PostGIS
* Docker Desktop (this should include Docker Compose)

1. Create a PostGIS-enabled database for the project
The psql command will vary slightly with different OSes. For Mac:
  
.. code-block:: bash

    psql -d postgres

    CREATE DATABASE racial_covenants_processor;
    CREATE USER racial_covenants_processor with password 'racial_covenants_processor';
    GRANT ALL PRIVILEGES ON DATABASE racial_covenants_processor to racial_covenants_processor;
    ALTER DATABASE racial_covenants_processor OWNER TO racial_covenants_processor;
    \q
    psql -d racial_covenants_processor
    CREATE EXTENSION postgis;


2. Install Python environment

.. code-block:: bash

    pipenv install

3. Create a ``.pg_service.conf`` file in your user home directory (not the application root directory). This creates a Postgresql service to connect between Django and the database. Add the following to the new file:

.. code-block::

    [deeds_service]
    host=localhost
    user=racial_covenants_processor
    dbname=racial_covenants_processor
    port=5432

4. Create your Django settings file:

.. code-block:: bash
    
    cp racial_covenants_processor/settings/local_settings.py.sample racial_covenants_processor/settings/local_settings.py

  
5. Sync Django with your database

.. code-block:: bash

    pipenv shell
    python manage.py migrate

6. To be able to view the admin pages, create a superuser

.. code-block:: bash

    python manage.py createsuperuser

7. For search to work, run a local OpenSearch instance in Docker. With Docker Desktop running:

.. code-block:: bash

    docker run -d --name opensearch-dev \
        -p 9200:9200 -p 9600:9600 \
        -e "discovery.type=single-node" \
        -e "DISABLE_SECURITY_PLUGIN=true" \
        opensearchproject/opensearch:2

The OpenSearch API endpoint will be available at `http://127.0.0.1:9200/<http://127.0.0.1:9200/>`__. The ``DISABLE_SECURITY_PLUGIN`` flag keeps local setup simple by serving plain HTTP with no authentication; production uses an Amazon OpenSearch Service domain with fine-grained access control.

8. Create a new .env file in the root directory (i.e. outside of `racial_covenants_processor/` and next to the Pipfile):

.. code-block:: bash

    cp .env.example .env

Set ``OPENSEARCH_URL=http://localhost:9200`` in the .env file. For the local no-auth container above you can leave ``OPENSEARCH_PASSWORD`` blank; setting it (to any value locally, or the master-user password for an Amazon OpenSearch domain) is what enables real-time indexing on save. When it is unset, the index is populated only via the management commands in step 10. You may need to kill and restart your pipenv shell for the new environment variables to be available:

.. code-block:: bash

    exit
    pipenv shell

9. Spin up the application

.. code-block:: bash

    python manage.py runserver

You can view the app at `http://127.0.0.1:8000/<http://127.0.0.1:8000/>`__.

10. Seed the search index. After loading data (for example a dump of the deployed database), create the index and populate it:

.. code-block:: bash

    python manage.py opensearch index create
    python manage.py opensearch document index

``opensearch index rebuild`` deletes and recreates the index mapping but does not re-populate it, so follow it with ``opensearch document index``. Add ``--parallel`` to the document command to speed up bulk indexing of large datasets.