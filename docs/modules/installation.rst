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

7. For search to work properly, you will need to set up Elasticsearch locally in a Docker container. With Docker Desktop running, run the following command to start the Elasticsearch container:

.. code-block:: bash

    curl -fsSL https://elastic.co/start-local | sh

The Elasticsearch API endpoint will be available at `http://127.0.0.1:9200/<http://127.0.0.1:9200/>`__ and the Kibana dashboard will be available at `http://127.0.0.1:5601/<http://127.0.0.1:5601/>`__.

8. Note the Elasticsearch authentication credentials in your terminal. They should look something like:

.. code-block:: bash
    🎉 Congrats, Elasticsearch and Kibana are installed and running in Docker!

    🌐 Open your browser at http://localhost:5601

    Username: elastic
    Password: <password>

    🔌 Elasticsearch API endpoint: http://localhost:9200
    🔑 API key: <api_key>

Create a new .env file in the root directory (i.e. outside of `racial_covenants_processor/` and next to the Pipfile):

.. code-block:: bash

    cp .env.example .env

Populate `ELASTICSEARCH_PASSWORD` and `ELASTICSEARCH_API_KEY` in the .env file using the credentials from the terminal output. Note: you may need to kill and restart your pipenv shell for the new environment variables to be available:

.. code-block:: bash

    exit
    pipenv shell

9. Spin up the application

.. code-block:: bash

    python manage.py runserver

You can view the app at `http://127.0.0.1:8000/<http://127.0.0.1:8000/>`__.

10. Any newly created records will be indexed on save. But, if you want to seed your database with a dump of the deployed database, you will need to run this command to index all those records:

.. code-block:: bash

    python manage.py search_index --rebuild