# Contributing Guidelines

## Contributions

Before contributing, make sure you mention you'll be working on it in the associated ticket. Open a new ticket if there's none about it.

We have a very limited number of contributors so rules are quite limited:

- Submit your changes over a Pull Request
- Make sure all your python code is black formatted.
- Make sure Codefactor reports no issue.
- API code (backend/dispatcher) must be tested. Make sure your PR doesn't decrease code coverage.

## Local setup

Setting up the zimfarm locally is a bit complicated due to the number of moving parts. But you don't need all of those depending on what you plan on working on.

You'll need [docker](https://www.docker.com/) and [python3.8](https://www.python.org/) for almost all parts so secure that first.

### backend API

* Install [mongodb](https://www.mongodb.com/)
* Setup a python3 environment
* `pip install dispatcher/backend/requirements.txt`
* Create initial user

```sh
cd dispatcher/backend/src
export INIT_USERNAME="admin"
export INIT_PASSWORD="admin_pass"
python -c "from utils.database import Initializer; Initializer.create_initial_user()"
```

* Create yourself a startup script like

``` sh
cd dispatcher/backend/src
export BINDING_HOST="0.0.0.0"
# set port on which you want the API to listen to. different than UI
export BINDING_PORT="80"
python main.py
```

* start your server
* Test your credentials

``` sh
# get a token
curl -X POST "http://localhost/v1/auth/authorize" -H  "accept: application/json" -H  "Content-Type: application/x-www-form-urlencoded" -d "username=admin&password=admin_pass"
# test your token
curl -I -X GET "http://localhost/v1/auth/test" -H  "accept: */*" -H  "token: eyJ0eXAxxxxxxx"
# verify that the response is HTTP/1.0 204 NO CONTENT
```

you now have a working backend with an admin user at http://127.0.0.1/v1

### import schedules backup

* Download a copy of the production schedules
``` sh
curl https://api.farm.openzim.org/v1/schedules/backup/ > all_schedules.json
```
* import those into your mongo database

```sh
cd dispatcher/backend/src
python
```

* Type-in the following code to import it

```py
import json
import pathlib

import bson

from common import mongo

# delete existing
mongo.Schedules().drop()
# create collection
mongo.Schedules().initialize()

with open(pathlib.Path("dump_schedules.json"), "r") as backup:
    for backup_schedule in json.load(backup):
        backup_schedule.update({"_id": bson.ObjectId(backup_schedule["_id"])})
        mongo.Schedules().insert_one(backup_schedule)
        print(f"inserted {backup_schedule['name']}")
```

You're all set!

## frontend-ui

You will need [nodejs](https://nodejs.org/) and [yarn](https://classic.yarnpkg.com/en/docs/install/) to work on the UI.

You can test your UI changes over the production zimfarm but if you are testing features that act on data, you will want to test over a local backend API.

Set your local backend url on `environ.js` so that the UI points to it:

```sh
echo 'var environ = {"ZIMFARM_WEBAPI": "http://127.0.0.1/v1"};' > dispatcher/frontend-ui/public/environ.js
```

* Setup your environment

```sh
cd cd dispatcher/frontend-ui
yarn install
```

* Create yourself a startup script

```sh
cd dispatcher/frontend-ui
# this will start UI on localhost:8080
yarn serve
```

You may want to disable CORS for your tests. Chromium can be launched with `--disable-web-security` for that.


## uploader

Uploader is a single Python file that has an optional dependency on [humanfriendly](https://pypi.org/project/humanfriendly/) (install it!).

You can test it on any SSH/SFTP server but we may want to ensure it works fine with our receiver.

## receiver

Given the very nature of the receiver (an SSHD server), it is only tested through its container.

* Create placeholder folders

```sh
# get list of folders from http://download.kiwix.org/zim/
mkdir -p $(pwd)/{mnt,jail}/zim/{gutenberg,other,phet,psiram,stack_exchange,ted,vikidia,wikibooks,wikinews,wikipedia,wikiquote,wikisource,wikispecies,wikiversity,wikivoyage,wiktionary}
```

* Test your changes via:

```sh
docker build receiver -f receiver/Dockerfile -t receiver
# use a local IP that docker can reach so not 127.0.0.1
docker -v $(pwd)/jail:/jail -v $(pwd)/mnt:/mnt run -e ZIMFARM_WEBAPI="http://192.168.5.80/v1 receiver"
```

## worker

It is recommended to read the [workers README](./workers/README.md) to understand all the configuration variables available.

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
	--env ZIMFARM_CPUS='3' \
	--env ZIMFARM_MEMORY='2G' \
	--env ZIMFARM_DISK='2G' \
	--env SELFISH="y" \
	--env USERNAME='admin' \
	--env DEBUG=1 \
	--env WORKER_NAME="myworker" \
	--env POLL_INTERVAL="30" \
	--env PLATFORM_wikimedia_MAX_TASKS="1" \
	--env PLATFORM_youtube_MAX_TASKS="1" \
   --env WEB_API_URI="http://192.168.5.80/v1" \
	--env TASK_WORKER_IMAGE='task-worker:local' \
	worker-manager:local
```

You can also test it over the production API (adjusting your credentials) with

```sh
	--env WEB_API_URI="https://api.farm.openzim.org/v1" \
```

