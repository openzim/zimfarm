#!/usr/bin/env bash

git pull
export SYSTEM_PASSWORD=`pwgen -Bs1 12`
docker-compose up --build -d