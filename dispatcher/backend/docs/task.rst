================
Tasks
================

mwoffliner
-----

::

    POST /api/task/mwoffliner

queue a task to mwoffliner

Request:
    Header:
        - token (admin token) 
 
    Body:
    ::

        {
            "mwoffliner": {
		        "mwUrl": "wikipedia.com",
		        "adminEmail": "admin@email.com" 
            }
        }
Response:
    
Tasks
-----

::

    GET /api/task/?<OPTIONS> 

view current tasks

Request:
    Header:
        - token
 
Response:
