This is a tentative docker-compose configuration to be used **only** for development purpose.

It is recommended to use it in combination with Mutagen to efficiently sync data from your machine to the Docker containers.

It is still incomplete (not all Zimfarm components are available).

## List of containers

### backend

This container is a backend web server, linked to its database.

### backend-tests

This container is simply a Python stack with all backend requirements but no web server. Context is
setup with appropriate environment variables for tests (i.e. it uses the test DB). Useful to run
tests locally.

### postgresqldb

This container is a PostgreSQL DB. DB data is kept in a volume, persistent across containers restarts.

### frontend-ui

This container hosts the frontend UI for end-users.

### receiver

This container hosts a customized SSH server, used to receive Zimfarm ZIMs coming from workers.

### worker_mgr

This container is the main worker container, responsible to start tasks. It is commented by default.

### task_worker

This container is a sample task executor. It is commented by default.

### watcher

This container is a StackExchange dumps watcher.

## Instructions

First start the Docker-Compose stack:

```sh
cd dev
docker compose -p zimfarm up --build -d
```

This sets up the containers, runs the migrations and creates an admin user with usernameset to `INIT_USERNAME` and password `INIT_PASSWORD`. See the backend environment variables

Note that to run integration tests, we use a separate DB with the backend-tests container

### Restart the backend

The backend might typically fail if the DB schema is not up-to-date, or if you create some nasty bug while modifying the code.

Restart it with:

```sh
docker restart zf_backend
```

Other containers might be restarted the same way.

### Browse the web UI

To develop: open [the development web UI](http://localhost:8002). This version has hot reload of UI code changes.

To test build version: open [the web UI](http://localhost:8001) in your favorite browser.

You can login with username `admin` and password `admin`.

### Run backend tests

```sh
docker exec -it zf_postgresdb dropdb -e -U zimfarm zimtest
docker exec -it zf_postgresdb psql -e -U zimfarm -c "CREATE DATABASE zimtest;"
docker exec -it zf_postgresdb psql -e -d zimtest -U zimfarm -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
```

Start a shell in the backend-tests container.

```sh
docker exec -it zf_backend-tests pytest -v
```

You can select one specific set of tests by path

```sh
docker exec -it zf_backend-tests pytest -v tests/routes/test_user.py
```

Or just one specific test function

```sh
docker exec -it zf_backend-tests pytest -v tests/routes/test_user.py -k test_list_users_no_auth
```

### Creating offliners and offliner definitions

In order to create recipes and request tasks, you need to seed the database with offliners and offliner definitions

A helper script to pull the latest offliner definitions from their respective repositories is at `contrib/create-offliners.sh`; call it once to authorize with the backend,
fetch the latest offliner definitions, create the offliners and their respective definitions accordingly. Once this is done, you can start creating recipes either via the API based on the offliner definition.

```sh
cd dev/contrib

./create-offliners.sh
```

### create a test worker

In order to test worker manager and task worker, but also to test some other stuff, you will need to have a test worker.

It is not mandatory to have the worker manager running in most situation, but you will need to have both a worker user in the Zimfarm, and associated private/public key pairs.

A useful script to perform all the test worker creation is at `contrib/create_worker.sh`: call it once to create a `test_worker` user, the associated worker object, and upload a test public key. You will then be able to assign tasks to this worker in the UI, and use this test worker for running the worker manager and the task worker.

```sh
cd dev/contrib

./create_worker.sh
```

Once this is is done, you can start the worker manager simply by running:

```sh
docker compose -p zimfarm --profile worker up --build -d
```

**Important:** Beware that once you start the worker manager, any pending task will be automatically started by the worker manager. You might want to clear the pending tasks list before starting the worker manager.

### import recipes backup

It is possible to download and import a backup of production recipes, so that you have
some data locally to test the UI for instance.

- Exec into the backend container

```sh
docker exec -it zf-backend bash
```

- Download the production recipes and store in `/tmp/all_recipes.json`. This might take
  a couple of minutes. Note, all passwords and secrets are greyed out, so you will likely
  need to go the editor UI to modify recipes that need passwords (perhaps set them to empty)

```sh
curl -fsSL https://api.farm.openzim.org/v2/recipes/backup -o /tmp/all_recipes.json
```

- Import the recipes into your local database

```sh
python3 /app/import_recipes.py /tmp/all_recipes.json
```

### mark a task as started

Through the UI, it is easy to create a requested task for your test worker. However, if you do not want to run the worker manager because you do not want the task to really proceed, it gets complicated to fake the start this requested task, i.e mark the fact that the test worker manager has reserved this requested task.

A useful script is at `contrib/start_first_req_task.sh`: this will mark the first task in the pipe (oldest one) as reserved for the test worker, and hence transform the requested task into a task. You can obviously call it many times to reserve many tasks. The script displays the whole task, including its id.

### tweak receiver configuration

Receiver is responsible to receive ZIMs, logs and artifacts created by the task worker. It is a modified SSH server which performs authentication against the Zimfarm DB.

In order to use it with a task manager, you have to create one directory per warehouse path (or at least create the ones for the tasks you will run).

A useful script has been added to the dev stack to create these directories:

```

docker exec -it zf_receiver /contrib/create-warehouse-paths.sh

```

### test a task manager

You can start a task manager manually simply by requesting a task in the UI and starting it manually (see above).

Once the task is reserved for the `test_worker`, you can modify the `task_worker` container `command` in `docker-compose.yml` with this ID, uncomment the `task_worker` section and start it.

### start a StackExchange dumps watcher

Uncomment the watcher configuration in docker-compose.yml

Setup a proper S3 url to a test bucket (including credentials in the URL)

By default, only beer.stackexchange.com domain dump is considered

Task are scheduled as in prod when a new dump is downloaded
