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

Authentication
--------------

To access the API users must authenticate themselves. There are currently two end-user methods for authentication available:

  - :ref:`User credentials <api-authentication-credentials>` (username and password) 
  - :ref:`User access Token <api-authentication-token>`

.. _api-authentication-credentials:

User credentials
````````````````

.. note::
  This method should not be used except for simple testing scenarios.

A user can authenticate themselves with their username and password. E.g. when using `curl` this can be done by using the `-u` command line parameter:

.. code-block:: bash

    curl -u "username:password" \
      "http://dtf.example.com/api/projects/4"

.. _api-authentication-token:

User access Token
`````````````````

.. note::
  There is not yet any front-end functionality for a user to create tokens.

A user can authenticate themselves with a specific token, unique to each user. This token needs to be passed in the *header* of requests. E.g. when using `curl` this can be done by using the `--header` command line parameter:

.. code-block:: bash

    curl --header "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
      "http://dtf.example.com/api/projects/4"

API Overview
------------

:doc:`Projects <api/projects>`

:doc:`Submissions <api/submissions>`

:doc:`Test Results <api/test_results>`

:doc:`References <api/references>`

:doc:`Users <api/users>`

.. toctree::
   :hidden:

   api/projects
   api/submissions
   api/test_results
   api/references
   api/users
