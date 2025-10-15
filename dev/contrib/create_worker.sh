#!/bin/bash

# Call it once to create a `test_worker`:
# - retrieve an admin token
# - create the `test_worker`` user
# - create the associated worker object
# - upload a test public key.
#
# To be used to have a "real" test worker for local development, typically to start
# a worker manager or a task manager or simply assign tasks to a worker in the UI/API

set -e

echo "Retrieving admin access token"

ZF_ADMIN_TOKEN="$(curl -s -X 'POST' \
    'http://localhost:8000/v2/auth/authorize' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{"username": "admin", "password": "admin"}' \
    | jq -r '.access_token')"

echo "Create test_worker user"

curl -s -X 'POST' \
  'http://localhost:8000/v2/users' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ZF_ADMIN_TOKEN" \
  -d '{
  "role":"worker",
  "username": "test_worker",
  "email":"test_worker@acme.com",
  "password":"test_worker"
}'

echo "Retrieving test_worker access token"

ZF_USER_TOKEN="$(curl -s -X 'POST' \
    'http://localhost:8000/v2/auth/authorize' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{"username": "test_worker", "password": "test_worker"}' \
    | jq -r '.access_token')"

echo "Worker check-in (will create it since missing)"

curl -s -X 'PUT' \
  'http://localhost:8000/v2/workers/test_worker/check-in' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ZF_USER_TOKEN" \
  -d '{
  "username": "test_worker",
  "cpu": 3,
  "memory": 1024,
  "disk": 0,
  "offliners": [
    "zimit",
    "ted",
    "phet",
    "mwoffliner",
    "openedx",
    "sotoki",
    "freecodecamp",
    "ifixit"
  ]
}'

echo "Generating SSH key pair (Ed25519)"
ssh-keygen -t ed25519 -f id_ed25519 -N ""
payload="$(jq -n --arg key "$(< id_ed25519.pub)" '{key: $key}')"


curl -X POST http://localhost:8000/v2/users/test_worker/keys \
  -H 'accept: */*' \
  -H "Authorization: Bearer $ZF_USER_TOKEN" \
  -H 'Content-Type: application/json; charset=utf-8' \
  -d "$payload"

echo "DONE"
