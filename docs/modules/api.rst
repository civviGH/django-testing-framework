REST API
========

The Django Testing Framework exposes a powerful REST API which can be used to control all aspects of the web-server.

General usage
-------------

Currently all REST API endpoints start with the ``/api/`` prefix. As an example, let's assume you have hosted your Django Testing Framework instance at ``dtf.example.com``. A valid API request to the :ref:`projects <api-projects-list>` endpoint could look as follows:

.. code-block:: bash

    curl "http://dtf.example.com/api/projects"

Some API endpoints include parameters of the form ``:id``. These are to be replaced with the actual id of an existing object. E.g. a valid API request to the :ref:`projects/:id <api-projects-get>` endpoint could look as follows:

.. code-block:: bash

    curl "http://dtf.example.com/api/projects/4"

.. Authentication
.. --------------

API Overview
------------

:doc:`Projects <api/projects>`

:doc:`Submissions <api/submissions>`

:doc:`Test Results <api/test_results>`

:doc:`References <api/references>`

.. toctree::
   :hidden:

   api/projects
   api/submissions
   api/test_results
   api/references
