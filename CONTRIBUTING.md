# Contributing Guidelines

## Contributions

Before contributing, make sure you mention you'll be working on it in the associated ticket. Open a new ticket if there's none about it.

We have a very limited number of contributors so rules are quite limited:

- Submit your changes over a Pull Request
- Make sure all your python code is black formatted.
- Make sure Codefactor reports no issue.
- API code (backend) must be tested. Make sure your PR doesn't decrease code coverage.

## Local setup

Setting up the zimfarm locally is a bit complicated due to the number of moving parts. But you don't need all of those depending on what you plan on working on.

An alternate way to run all this locally (as described below) is to use a fully docker-based stack. See [dev](dev/README.md) folder for details.

You'll need [docker](https://www.docker.com/), [python3.13](https://www.python.org/) and [hatch](https://hatch.pypa.io/) for almost all parts so secure that first.

### backend API

- Install [PostgreSQL](https://www.postgresql.org/)
- Setup a python3 environment
- `cd backend/`
- `hatch shell`

- Create initial user

```sh
export INIT_USERNAME="admin"
export INIT_PASSWORD="admin_pass"
export JWT_SECRET="jwt_secret"
export POSTGRES_URI="database-dsn"

create-initial-user
```

- Start the server

```sh
uvicorn zimfarm_backend.main:app --reload --port 8000
```

- Test your credentials

```sh
# get a token
curl -X POST "http://localhost:8000/v2/auth/authorize" \
    -H  "accept: application/json" \
    -H  "Content-Type: application/application/json" \
    -d '{"usrname": "admin", "password": "admin_pass"}'
# test your token
curl -I -X GET "http://localhost:8000/v2/auth/test" -H  "accept: */*" -H  "Bearer: eyJ0eXAxxxxxxx"
# verify that the response is HTTP/1.0 204 NO CONTENT
```

you now have a working backend with an admin user at http://127.0.0.1:8000/v2

### import schedules backup

It is possible to download and import a backup of production schedules, so that you have some data
locally to test the UI for instance.

Detailed instructions are provided in the [Jupyter notebook](dev/import_schedules.ipynb), which must be ran from the same folder `backend/src`, with all dependencies installed.

## frontend-ui

You will need [nodejs](https://nodejs.org/) and [yarn](https://classic.yarnpkg.com/en/docs/install/) to work on the UI.

You can test your UI changes over the production zimfarm but if you are testing features that act on data, you will want to test over a local backend API.

Set your local backend url on `environ.js` so that the UI points to it:

```sh
echo 'var environ = {"ZIMFARM_WEBAPI": "http://127.0.0.1:8000/v2"};' > frontend-ui/public/environ.js
```

- Setup your environment

```sh
cd frontend-ui
yarn install
```

- Starting the frontend server

```sh
cd frontend-ui
# this will start UI on localhost:5173
yarn run dev
```

You may want to disable CORS for your tests. Chromium can be launched with `--disable-web-security` for that.

## uploader

Uploader is a single Python file that has an optional dependency on [humanfriendly](https://pypi.org/project/humanfriendly/) (install it!).

You can test it on any SSH/SFTP server but we may want to ensure it works fine with our receiver.

## receiver

Given the very nature of the receiver (an SSHD server), it is only tested through its container.

- Create placeholder folders

```sh
# get list of folders from http://download.kiwix.org/zim/
mkdir -p $(pwd)/{mnt,jail}/zim/{gutenberg,other,phet,psiram,stack_exchange,ted,vikidia,wikibooks,wikinews,wikipedia,wikiquote,wikisource,wikispecies,wikiversity,wikivoyage,wiktionary}
```

- Test your changes via:

```sh
docker build receiver -f receiver/Dockerfile -t receiver
# use a local IP that docker can reach so not 127.0.0.1
docker -v $(pwd)/jail:/jail -v $(pwd)/mnt:/mnt run -e ZIMFARM_WEBAPI="http://192.168.5.80/v1 receiver"
```

## worker

It is recommended to read the [workers README](./worker/README.md) to understand all the configuration variables available.

While it is possible to test the task-worker individually, we recommend to always test via a scheduled task using a manager, and always via docker.

Create yourself a startup script

```sh
cd workers
cont_name="zimfarm-manager"
echo "building task-worker"
docker build . -f task-Dockerfile -t task-worker:local || exit 1
echo "building working-manager"
docker build . -f manager-Dockerfile -t worker-manager:local || exit 1
docker rm $cont_name
docker run \
	--name $cont_name \
	-v $(pwd)/worker-data:/data \
	-v /var/run/docker.sock:/var/run/docker.sock:ro \
	-v /home/self/.ssh/zimfarm:/etc/ssh/keys/zimfarm:ro \
	--env ZIMFARM_CPUS="3" \
	--env ZIMFARM_MEMORY="2G" \
	--env ZIMFARM_DISK="2G" \
	--env SELFISH="true" \
	--env USERNAME="admin" \
	--env DEBUG="true" \
	--env WORKER_NAME="myworker" \
	--env POLL_INTERVAL="30" \
	--env PLATFORM_wikimedia_MAX_TASKS="1" \
	--env PLATFORM_youtube_MAX_TASKS="1" \
	--env PLATFORM_wikihow_MAX_TASKS="1" \
    --env WEB_API_URI="http://192.168.5.80/v2" \
	--env TASK_WORKER_IMAGE="task-worker:local" \
	worker-manager:local
```

You can also test it over the production API (adjusting your credentials) with

```sh
	--env WEB_API_URI="https://api.farm.openzim.org/v2" \
```
