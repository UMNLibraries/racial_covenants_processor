Installation
============

Django installation process
---------------------------

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

3. Create a Postgresql service to connect between Django and the DB called ``.pg_service.conf``

.. code-block::

    [deeds_service]
    host=localhost
    user=racial_covenants_processor
    dbname=racial_covenants_processor
    port=5432


4. Sync Django with your database

.. code-block:: bash

    pipenv shell
    python manage.py migrate


5. To be able to view the admin pages, create a superuser

.. code-block:: bash

    python manage.py createsuperuser
