Authorization
=====================================

All Zimfarm resource APIs require authorization. To prove identity, the request to resource APIs must include a valid access token in the Header field.

When access token become invalid, use the refresh token for a new access token and refresh token.

Tokens
-------------------------------------

Zimfarm use a short lived access token and a long lived refresh token.

access token
  - a jwt token
  - proves identity when interacting with resources
  - can be used multiple times
  - expires every 15 minutes
refresh token
  - a uuid4 token
  - proves identity when access token is lost or expires
  - one time use
  - expires every 30 days

Workflow
-------------------------------------

.. toctree::
   :maxdepth: 1

   authorize
   token