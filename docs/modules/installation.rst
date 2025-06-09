Installation
============

Django installation process
---------------------------

These steps assume you already have [the repo](https://github.com/UMNLibraries/racial_covenants_processor/tree/main) cloned and the following installed:
- Python 3.12
- pipenv
- gdal
- PostgreSQL
- PostGIS

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

.. code-block::
    cp racial_covenants_processor/settings/local_settings.py.sample racial_covenants_processor/settings/local_settings.py


5. Sync Django with your database

.. code-block:: bash

    pipenv shell
    python manage.py migrate


6. To be able to view the admin pages, create a superuser

.. code-block:: bash

    python manage.py createsuperuser

7. Spin up the application

.. code-block:: bash
    python manage.py runserver

You can view the app at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
