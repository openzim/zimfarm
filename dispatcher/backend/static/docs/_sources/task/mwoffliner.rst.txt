:tocdepth: 1

Schedule MWOffliner Tasks
=====================================

Use this API to schedule MWOffliner tasks. Dispatcher performs a check on all task configurations. The check process is atomic, as in, if one configuration is invalid, none of the tasks in the request will be added. 

Request
-------------------------------------

Endpoint
  **POST** /api/task/mwoffliner
Header
  - access-token: str
Body
  Each MWOfflinerConfig object creates a task

  .. code-block:: javascript

    [
        MWOfflinerConfig
    ]

Response
-------------------------------------

Status code
  202
Header
  Content-Type: application/json
Body
  .. code-block:: javascript

    [
        ObjectID, ...
    ]

Example
-------------------------------------

.. code-block:: bash

  curl -X "POST" "https://farm.openzim.org/api/task/mwoffliner" \
       -H 'token: ACCESS_TOKEN' \
       -H 'Content-Type: application/json; charset=utf-8' \
       -d $'[
    {
      "mwUrl": "https://bm.wikipedia.org/",
      "adminEmail": "user@example.com",
      "verbose": false
    },
    {
      "mwUrl": "https://da.wikipedia.org/",
      "adminEmail": "user@example.com",
      "verbose": true
    }
  ]'

.. _mwoffliner-config:

MWOffliner Config
-------------------------------------