:tocdepth: 1

List Tasks
=====================================

Get basic overview of tasks. Tasks created later appear first in the list. For each task, the following properties will be returned:

- _id
- status

- offliner:

  - name
  - config

- timestamp:

  - creation
  - termination

Request
-------------------------------------

Endpoint
  **GET** /api/task
URL Parameter
  - limit: int
  - offset: int
Header
  - token: str

Response
-------------------------------------

Header
  Content-Type: application/json
Body
  .. code-block:: json

    {
        "items": [
            {
                "_id": ObjectID, 
                "offliner": {
                    "config": {
                        "adminEmail": string, 
                        "mwUrl": string, 
                        "verbose": bool
                    }, 
                    "name": string
                }, 
                "status": string, 
                "timestamp": {
                    "creation": datetime, 
                    "termination": datetime
                }
            }, ...
        ],
        "meta": {
            "limit": integer, 
            "offset": integer
        }
    }

Example
-------------------------------------

.. code-block:: bash

  curl "https://farm.openzim.org/api/task/?limit=60" \
     -H 'token: ACCESS_TOKEN'