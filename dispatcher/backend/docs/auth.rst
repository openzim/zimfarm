================
 Authentication
================

Login
-----

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


Renew
-----

::

    POST /api/auth/renew

Renew token with a valid and non-expired JWT token

Request:
    Header:
        - token

Response:
    ::

        {
            "token": JWT_TOKEN
        }