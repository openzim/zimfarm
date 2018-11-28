#!/usr/bin/env bash

git pull

# create .env file if not exist
if [[ ! -f .env ]]
then
    touch .env
fi

if ! grep -q SYSTEM_PASSWORD .env
then
    sed -i -e 'SYSTEM_PASSWORD=${pwgen -Bs1 12}' .env
fi

docker-compose -f docker-compose2.yml up --build -d
