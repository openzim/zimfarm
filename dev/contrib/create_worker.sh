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

die() {
    echo "ERROR: $1" >&2
    exit 1
}

check_non_empty() {
    local arg="$1"
    local message="$2"
    if [ -z "$arg" ]; then
	die "${message}"
    fi
}

check_http_code() {
    local http_code="$1"
    local response="$2"

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
	:
    else
	error_msg=$(echo "$response" | jq -r '.errors // .message // .detail // "Unknown error"' 2>/dev/null || echo "HTTP $http_code")
	die "Could not checkin worker: ${error_msg}"
    fi
}

echo "Retrieving admin access token"

ZF_ADMIN_TOKEN="$(curl -s -X 'POST' \
    'http://localhost:8000/v2/auth/authorize' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{"username": "admin", "password": "admin"}' \
    | jq -r '.access_token')"

if [ -z "$ZF_ADMIN_TOKEN" ] || [ "$ZF_ADMIN_TOKEN" = "null" ]; then
    die "Failed to retrieve admin access token"
fi

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

if [ -z "$ZF_USER_TOKEN" ] || [ "$ZF_USER_TOKEN" = "null" ]; then
    die "Failed to retrieve worker access token"
fi

echo "Worker check-in with 1Gb memory, 1Gb disk and 1 CPU (modify script to use your custom values)"

response=$(curl -s -w "\n%{http_code}" -X 'PUT' \
  'http://localhost:8000/v2/workers/test_worker/check-in' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ZF_USER_TOKEN" \
  -d '{
  "username": "test_worker",
  "cpu": 1,
  "memory": 1073741824,
  "disk": 1073741824,
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
}')

http_code=$(echo "$response" | tail -n1)
response=$(echo "$response" | head -n -1)

check_http_code "$http_code" "$response"

echo "Generating SSH key pair (Ed25519)"
ssh-keygen -t ed25519 -f id_ed25519 -N ""
payload="$(jq -n --arg key "$(< id_ed25519.pub)" '{key: $key}')"


echo "Uploading worker keys to API"
response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/v2/users/test_worker/keys \
  -H 'accept: */*' \
  -H "Authorization: Bearer $ZF_USER_TOKEN" \
  -H 'Content-Type: application/json; charset=utf-8' \
  -d "$payload")

echo "Move/Copy the worker keys to where the worker manager can access it (typically a docker volume mount if you are running in a container)"

http_code=$(echo "$response" | tail -n1)
response=$(echo "$response" | head -n -1)

check_http_code "$http_code" "$response"

echo "DONE"
