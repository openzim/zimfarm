:tocdepth: 1

Get Task Detail
=====================================

Get task detail, including:

- _id
- status

- offliner:

  - name
  - config

- timestamp:

  - creation
  - termination

- logs

Request
-------------------------------------

Endpoint
  **GET** /api/task/<task_id: string>
Header
  - token: str

Response
-------------------------------------

Header
  Content-Type: application/json
Body
  .. code-block:: javascript

    {
        "_id": ObjectID,
        "status": string,
        "offliner": {
            "config": {
                "adminEmail": string, 
                "mwUrl": string, 
                "verbose": bool
            }, 
            "name": string
        },
        "timestamp": {
            "creation": datetime, 
            "termination": datetime
        },
        "log": [
            {
                "name": string,
                "success": bool,
                "std_out": string
            }
        ]
    }

Example
-------------------------------------

.. code-block:: bash

  curl "https://farm.openzim.org/api/task/5ac3e58b8acc5b0026271194" \
     -H 'token: ACCESS_TOKEN'