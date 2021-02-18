Projects API
============

.. _api-projects-list:

List projects
-------------

List all projects available on the server.

.. code-block:: bash

    GET /projects

An example could look as follows:

.. code-block:: bash

    curl -X GET \
      http://dtf.example.com/api/projects

which might give a result like this:

.. code-block::

    [
        {
            "id": 2,
            "name": "Demo Project",
            "slug": "demo"
        },
        {
            "id": 1,
            "name": "My Test Project",
            "slug": "my-test-project"
        }
    ]

.. _api-projects-new:

Create new project
------------------

Create a new, global project on the server.

.. code-block:: bash

    POST /projects

.. table::

    +----------------+----------------+----------+--------------------------------------------------------+
    | Attribute      | Type           | Required | Description                                            |
    +================+================+==========+========================================================+
    | `name`         | string         | yes      | The name of the project to create.                     |
    +----------------+----------------+----------+--------------------------------------------------------+
    | `slug`         | string         | yes      | Slug for the project to be used in the URL.            |
    |                |                |          | This needs to be a valid                               |
    |                |                |          | `slug <https://en.wikipedia.org/wiki/Clean_URL#Slug>`_ |
    |                |                |          | and it needs to be unique over all projects.           |
    +----------------+----------------+----------+--------------------------------------------------------+

An example could look as follows:

.. code-block:: bash

    curl -X POST \
      --header "Content-Type: application/json" \
      --data '{
                  "name": "My Test Project",
                  "slug": "my-test-project"
              }' \
      http://dtf.example.com/api/projects

.. _api-projects-get:

Get single project
------------------

Retrieve a specific project from the server.

.. code-block:: bash

    GET /projects/:id

.. table::

    +----------------+----------------+----------+--------------------------------------------------------+
    | Attribute      | Type           | Required | Description                                            |
    +================+================+==========+========================================================+
    | `:id`          | string/integer | yes      | The id or slug of the project.                         |
    +----------------+----------------+----------+--------------------------------------------------------+

An example using the id could look as follows:

.. code-block:: bash

    curl -X GET \
      http://dtf.example.com/api/projects/2

or using the project slug:

.. code-block:: bash

    curl -X GET \
      http://dtf.example.com/api/projects/demo

which might give a result like this:

.. code-block::

    {
        "id": 2,
        "name": "Demo Project",
        "slug": "demo"
    }

.. _api-projects-modify:

Modify single project
---------------------

Modify the fields of an existing project. All fields have to be given (even the ones that are unchanged).

.. code-block:: bash

    PUT /projects/:id

.. table::

    +----------------+----------------+----------+--------------------------------------------------------+
    | Attribute      | Type           | Required | Description                                            |
    +================+================+==========+========================================================+
    | `:id`          | integer/string | yes      | The id or slug of the project.                         |
    +----------------+----------------+----------+--------------------------------------------------------+
    | `name`         | string         | yes      | The new name of the project.                           |
    +----------------+----------------+----------+--------------------------------------------------------+
    | `slug`         | string         | yes      | The new slug of the project.                           |
    |                |                |          | This needs to be a valid                               |
    |                |                |          | `slug <https://en.wikipedia.org/wiki/Clean_URL#Slug>`_ |
    |                |                |          | and it needs to be unique over all projects.           |
    +----------------+----------------+----------+--------------------------------------------------------+

An example could look as follows:

.. code-block:: bash

    curl -X POST \
      --header "Content-Type: application/json" \
      --data '{
                  "name": "Demo Project New Name",
                  "slug": "demo-project"
              }' \
      http://dtf.example.com/api/projects/2

.. _api-projects-delete:

Delete single project
---------------------

Deletes a project and all associated data. This can not be undone!

.. code-block:: bash

    DELETE /projects/:id

.. code-block:: bash

    curl -X DELETE \
      http://dtf.example.com/api/projects/2

.. _api-projects-properties-list:

List project properties
-----------------------

.. code-block:: bash

    GET /projects/:project_id/properties

.. _api-projects-properties-new:

Add new project property
------------------------

.. code-block:: bash

    POST /projects/:project_id/properties

.. _api-projects-properties-get:

Get single project property
---------------------------

.. code-block:: bash

    GET /projects/:project_id/properties/:prop_id

.. _api-projects-properties-modify:

Modify project property
-----------------------

.. code-block:: bash

    PUT /projects/:project_id/properties/:prop_id

.. _api-projects-properties-delete:

Delete project property
-----------------------

.. code-block:: bash

    DELETE /projects/:project_id/properties/:prop_id
