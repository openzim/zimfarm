:tocdepth: 1

Regain access with Refresh Token
=====================================

When your access token is expired or lost, you can regain access to the system using a valid refresh token.

Note: if the refresh token is also expired, you have to re-authenticate with credentials

Request
-------------------------------------

Endpoint
  **POST** /api/auth/token
Header
  - refresh-token: REFRESH_TOKEN

Response
-------------------------------------

Header
  Content-Type: application/json
Body
  .. code-block:: javascript

    {
        "access_token": ACCESS_TOKEN,
        "refresh_token": REFRESH_TOKEN
    }

Example
-------------------------------------

.. code-block:: bash

  curl -X "POST" "https://farm.openzim.org/api/auth/token" \
     -H 'refresh-token: REFRESH_TOKEN'