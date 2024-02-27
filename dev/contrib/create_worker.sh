#!/bin/bash

set -e

echo "Retrieving admin access token"

ZF_ADMIN_TOKEN="$(curl -s -X 'POST' \
    'http://localhost:8000/v1/auth/authorize' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'username=admin&password=admin' \
    | jq -r '.access_token')"

echo "Create test_worker user"

curl -s -X 'POST' \
  'http://localhost:8000/v1/users/' \
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
    'http://localhost:8000/v1/auth/authorize' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'username=test_worker&password=test_worker' \
    | jq -r '.access_token')"

echo "Worker check-in (will create it since missing)"

curl -s -X 'PUT' \
  'http://localhost:8000/v1/workers/test_worker/check-in' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ZF_USER_TOKEN" \
  -d '{
  "username": "test_worker",
  "cpu": 3,
  "memory": 1024,
  "disk": 0,
  "offliners": [
    "zimit"
  ]
}'

echo "Add private key to test_worker"

curl -X POST http://localhost:8000/v1/users/test_worker/keys \
  -H 'accept: */*' \
  -H "Authorization: Bearer $ZF_USER_TOKEN" \
  -H 'Content-Type: application/json; charset=utf-8' \
  -d '{"name": "test_key", "key": "AAAAB3NzaC1yc2EAAAADAQABAAABAQCn2r5IZSJp02FBAYSZBQRdOBKBK2VOErdrBCZm5Ig3hDKQuxq38+W5CJ2JUJU+LQm//uenm58scGlEtk5+w5SjObjzK8Qx6JeRhAiZ8xpyydSoUIvd0ARD9OKwdiQFqVlLPlOyrdIpQ2vRESdwzhe0f7EYUwgKzBw5k0foxQsGxTiztY/ugWJ8Jso5WOxXwzEw4cSnGhdrehqLphlZanr54wj5oTcrj/vJHlpbxkYzFMc2Zgj81GdIV4yP3H1yX4ySK8VkDPOCczHacdRnHw4u8Vgf6wS6Zy3iMpvuGu7BJkwNoTXvmVV5BXUm6GAMSQTAPcw5T8M+eXjSAnriGDAL"}'

echo "DONE"