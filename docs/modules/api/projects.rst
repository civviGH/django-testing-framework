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

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects-POST-attributes.csv
   :delim: |

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

.. literalinclude :: generated/projects/projects_id-GET-desc.txt

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id-GET-attributes.csv
   :delim: |

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

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id-PUT-attributes.csv
   :delim: |

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

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id-DELETE-attributes.csv
   :delim: |

An example could look as follows:

.. literalinclude :: generated/projects/projects_id-DELETE-curl.sh
   :language: bash

.. _api-projects-properties-list:

List project properties
-----------------------

List all properties of a given project.

.. literalinclude :: generated/projects/projects_id_properties-GET-desc.txt

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id_properties-GET-attributes.csv
   :delim: |

An example could look as follows:

.. literalinclude :: generated/projects/projects_id_properties-GET-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/projects/projects_id_properties-GET-response.json
   :language: json

.. _api-projects-properties-new:

Add new project property
------------------------

Add a new property to a project.

.. literalinclude :: generated/projects/projects_id_properties-POST-desc.txt

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id_properties-POST-attributes.csv
   :delim: |

An example could look as follows:

.. literalinclude :: generated/projects/projects_id_properties-POST-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/projects/projects_id_properties-POST-response.json
    :language: json


.. _api-projects-properties-get:

Get single project property
---------------------------

Retrieve a specific property from a project.

.. literalinclude :: generated/projects/projects_id_properties_id-GET-desc.txt

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id_properties_id-GET-attributes.csv
   :delim: |

An example could look as follows:

.. literalinclude :: generated/projects/projects_id_properties_id-GET-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/projects/projects_id_properties_id-GET-response.json
   :language: json

.. _api-projects-properties-modify:

Modify project property
-----------------------

Modify the fields of an existing properties. All fields have to be given (even the ones that are unchanged).

.. literalinclude :: generated/projects/projects_id_properties_id-PUT-desc.txt

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id_properties_id-PUT-attributes.csv
   :delim: |

An example could look as follows:

.. literalinclude :: generated/projects/projects_id_properties_id-PUT-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/projects/projects_id_properties_id-PUT-response.json
    :language: json

.. _api-projects-properties-delete:

Delete project property
-----------------------

Deletes a property from a project. This can not be undone!

.. literalinclude :: generated/projects/projects_id_properties_id-DELETE-desc.txt

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id_properties_id-DELETE-attributes.csv
   :delim: |

An example could look as follows:

.. literalinclude :: generated/projects/projects_id_properties_id-DELETE-curl.sh
   :language: bash

List project members
--------------------

List all members of a given project.

.. literalinclude :: generated/projects/projects_id_members-GET-desc.txt

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id_members-GET-attributes.csv
   :delim: |

An example could look as follows:

.. literalinclude :: generated/projects/projects_id_members-GET-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/projects/projects_id_members-GET-response.json
   :language: json

.. _api-projects-members-new:

Add new project member
----------------------

Add a new member to a project.

.. literalinclude :: generated/projects/projects_id_members-POST-desc.txt

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id_members-POST-attributes.csv
   :delim: |

An example could look as follows:

.. literalinclude :: generated/projects/projects_id_members-POST-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/projects/projects_id_members-POST-response.json
    :language: json


.. _api-projects-members-get:

Get single project member
-------------------------

Retrieve a specific member from a project.

.. literalinclude :: generated/projects/projects_id_members_id-GET-desc.txt

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id_members_id-GET-attributes.csv
   :delim: |

An example could look as follows:

.. literalinclude :: generated/projects/projects_id_members_id-GET-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/projects/projects_id_members_id-GET-response.json
   :language: json

.. _api-projects-members-modify:

Modify project member
---------------------

Modify the fields of an existing members. All fields have to be given (even the ones that are unchanged).

.. literalinclude :: generated/projects/projects_id_members_id-PUT-desc.txt

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id_members_id-PUT-attributes.csv
   :delim: |

An example could look as follows:

.. literalinclude :: generated/projects/projects_id_members_id-PUT-curl.sh
   :language: bash

which might give a result like this:

.. literalinclude :: generated/projects/projects_id_members_id-PUT-response.json
    :language: json

.. _api-projects-members-delete:

Delete project member
---------------------

Deletes a member from a project. This can not be undone!

.. literalinclude :: generated/projects/projects_id_members_id-DELETE-desc.txt

.. csv-table::
   :header-rows: 1
   :file: generated/projects/projects_id_members_id-DELETE-attributes.csv
   :delim: |

An example could look as follows:

.. literalinclude :: generated/projects/projects_id_members_id-DELETE-curl.sh
   :language: bash

.. _api-projects-members-list:
