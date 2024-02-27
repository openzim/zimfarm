#!/bin/bash

set -e

echo "Retrieving access token"

ZF_ADMIN_TOKEN="$(curl -s -X 'POST' \
    'http://localhost:8000/v1/auth/authorize' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'username=admin&password=admin' \
    | jq -r '.access_token')"

echo "Get last requested task"

FIRST_TASK_ID="$(curl -s -X 'GET' \
  'http://localhost:8000/v1/requested-tasks/' \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $ZF_ADMIN_TOKEN" \
  | jq -r '.items[0]._id')"

if [ "$FIRST_TASK_ID" = "null" ]; then
    echo "No pending requested task. Exiting script."
    exit 1
fi

echo "Start task (i.e. mark it as started)"

curl -s -X 'POST' \
  "http://localhost:8000/v1/tasks/$FIRST_TASK_ID?worker_name=worker" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $ZF_ADMIN_TOKEN" \
  -d ''

echo "DONE"