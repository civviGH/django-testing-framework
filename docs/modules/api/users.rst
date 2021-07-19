Users API
=========

.. _api-users-list:

List users
-------------

List all users available on the server.

.. literalinclude :: generated/users/users-GET-desc.txt

An example could look as follows:


.. literalinclude :: generated/users/users-GET-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/users/users-GET-response.json
   :language: json


.. _api-users-get:

Get single user
----------------

Retrieve a specific user from the server.

.. literalinclude :: generated/users/users_id-GET-desc.txt

.. csv-table::
   :header-rows: 1
   :file: generated/users/users_id-GET-attributes.csv
   :delim: |

An example could look as follows:

.. literalinclude :: generated/users/users_id-GET-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/users/users_id-GET-response.json
   :language: json
