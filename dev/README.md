This is a tentative docker-compose configuration to be used **only** for development purpose.

It is recommended to use it in combination with Mutagen to effeciently sync data from your machine to the Docker containers.

It is mostly incomplete.

## backend

This container is a backend web server, linked to its database.

## backend-tools

This container is simply a Python stack with all backend requirements but no web server. Context is
setup with appropriate environment variables. Usefull for instance to run alembic.

## backend-tests

This container is simply a Python stack with all backend requirements but no web server. Context is
setup with appropriate environment variables for tests (i.e. it uses the test DB). Usefull to run
tests locally.

## postgresqldb

This container is a PostgreSQL DB. DB data is kept in a volume, persistent across containers restarts.

## mongodb

This container is a Mongo DB.