================
 Authentication
================
::

    POST /api/auth/login

Login and get a token using username and password.

Request:
    Header:
        - username
        - password

Response:
    ::

        {
            "token": JWT_TOKEN
        }
