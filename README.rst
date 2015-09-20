django-db-quick-setup
=====================

.. image:: https://travis-ci.org/amezin/django-db-quick-setup.svg
    :target: https://travis-ci.org/amezin/django-db-quick-setup

Create and start MySQL/PostgreSQL containers with a single management command.

* If an image isn't available, it will be pulled.
* If a container with the specified configuration doesn't exist, it will be
  created.
* If a container is not running, it will be started.

Necessary settings are taken from settings.py.

* SQLite databases are ignored.
* For MySQL and PostgreSQL, one container is created per database.

Also, Docker settings are picked up from standard ``DOCKER\_\*`` environment
variables.


Usage
-----

.. code:: shell

    ./manage.py db_quick_setup

``'db_quick_setup'`` should be added to ``INSTALLED_APPS``:

.. code:: python

    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.admin',
        'db_quick_setup'
    )

``'HOST'`` in database settings should point to Docker hostname/IP. You can
use `find_docker_host()` to auto-detect it.

.. code:: python

    from db_quick_setup import find_docker_host

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'mysql_db',
            'USER': 'mysql_db',
            'PASSWORD': 'mysql_db_pass',
            'HOST': find_docker_host(),
            'PORT': 53308
        }
    }

``'NAME'``, ``'USER'``, ``'PASSWORD'`` and ``'PORT'`` can have arbitrary names,
the container will be configured accordingly.

Settings
--------

``DOCKER_MYSQL_IMAGE``: Docker image to use for MySQL databases. Default is the
official image - ``mysql:latest``.

``DOCKER_POSTGRES_IMAGE``: Docker image for PostgreSQL databases. Default is
the official image - ``postgresql:latest``.

``DOCKER_ASSERT_HOSTNAME``: look at Docker documentation.

``DOCKER_PRIVILEGED``: create privileged containers. Currently used as a
workaround for permission problems on Travis CI. It is disabled by default,
and shouldn't be enabled usually.
