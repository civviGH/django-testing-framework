Projects API
============

.. _api-projects-list:

List projects
-------------

List all projects available on the server.

.. literalinclude :: generated/projects/projects-GET-desc.txt

An example could look as follows:


.. literalinclude :: generated/projects/projects-GET-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/projects/projects-GET-response.json
   :language: json

.. _api-projects-new:

Create new project
------------------

Create a new, global project on the server.

.. literalinclude :: generated/projects/projects-POST-desc.txt

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

.. literalinclude :: generated/projects/projects-POST-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/projects/projects-POST-response.json
    :language: json

.. _api-projects-get:

Get single project
------------------

Retrieve a specific project from the server.

.. literalinclude :: generated/projects/projects_id-GET-primary_key-desc.txt

.. table::

    +----------------+----------------+----------+--------------------------------------------------------+
    | Attribute      | Type           | Required | Description                                            |
    +================+================+==========+========================================================+
    | `:id`          | string/integer | yes      | The id or slug of the project.                         |
    +----------------+----------------+----------+--------------------------------------------------------+

An example using the id could look as follows:

.. literalinclude :: generated/projects/projects_id-GET-primary_key-curl.sh
   :language: bash

or using the project slug:

.. literalinclude :: generated/projects/projects_id-GET-slug-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/projects/projects_id-GET-slug-response.json
   :language: json

.. _api-projects-modify:

Modify single project
---------------------

Modify the fields of an existing project. All fields have to be given (even the ones that are unchanged).

.. literalinclude :: generated/projects/projects_id-PUT-desc.txt

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

.. literalinclude :: generated/projects/projects_id-PUT-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/projects/projects_id-PUT-response.json
    :language: json

.. _api-projects-delete:

Delete single project
---------------------

Deletes a project and all associated data. This can not be undone!


.. literalinclude :: generated/projects/projects_id-DELETE-desc.txt

An example could look as follows:

.. literalinclude :: generated/projects/projects_id-DELETE-curl.sh
   :language: bash

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
