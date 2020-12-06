Quickstart Guide
================

Example installation for \*nix
------------------------------

To install the server just unpack the source code into the folder you want the server to run in, or just git to clone the most recent version of DTF.

.. note::
    If you use the default SQL backend SQLite3 the database will also be saved in that folder. Make sure you have enough disk space available

.. code-block:: bash

    tar xf dtf.tar
    cd dtf

Using a python virtual environment to install packages with pip is recommended

.. code-block:: bash

    virtualenv -p python3 env
    source env/bin/activate

You should have the following files in your folder:

.. code-block:: console

    docs  env           manage.py         rest
    dtf   initial.json  requirements.txt

Install all the python package requirements, create the database and start the server:

.. code-block:: bash

    pip install -r requirements.txt
    python manage.py migrate
    python manage.py runserver

By default, the server is only available locally and starts on port 8000. You can specify the bind ip as well as the port when starting the server:

.. code-block:: bash

    python manage.py runserver 0.0.0.0:80

The server is then reachable for all hosts on the network under the default HTTP port 80.

Using the API
-------------