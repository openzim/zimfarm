# ZIM Farm

The ZIM farm (zimfarm) is a half-decentralised software solution to
build ZIM files (http://www.openzim.org/) efficiently. This means scrapping Web contents,
packaging them into a ZIM file and uploading the result to an online
ZIM files repository.

## Principle

The whole zimfarm system works as a task scheduler and is made of two components:

* The **dispatcher**, the central node, which takes and dispatches zim file generation
  tasks. It is managed by the openZIM project admin and
  hosted somewhere on the Internet.

* The **workers**, task executers, which are hosted by
  openZIM volunteers in different places around the world through Internet.

To get a new ZIM file the typical workflow is:

1. User submits a new task (to get a specific ZIM file made).
2. Dispatcher enqueues the task.
3. A worker pulls the task.
4. Worker generates the ZIM file and upload it.

## Run the system as a whole

1. Make sure docker and docker-compose are installed on your system
2. Clone this repo
3. Make sure you are in master branch
4. Open a terminal session change directory to root of this repo
5. Run `docker-compose up --build`
6. Wait for docker to do its job
7. Go to `http://localhost:8080` with your Web browser

## Architecture

The whole system is build by reusing the best of free software
libraries components. The whole ZIM farm solutioon itself is made
available using Docker images.

Actually, we use even more Docker images, as the ZIM file are produced
in dedicated custom Docker images the worker has to "invoke" depending
of the properties of the task he has to accomplish.

### Softwares

Dispatcher:
- proxy: nginx
  - frontend: angular 2, Node.js
  - backend: flask, celery, sqlite, python
- messaging queue: RabbitMQ

Worker:
- python
- docker

### Example of API request

Login and get a token:
```
$ curl -i -X POST -H "username: foo" -H "password: bar" "https://farm.openzim.org/api/auth/login"
```

Request a creation of ZIM file::
```
curl -i -X POST -H "Content-Type: application/json; charset=utf-8" -H "token: eyJ0eXAiOiJK..." --data "[{ \"mwUrl\": \"https://bm.wikipedia.org/\", \"adminEmail\": \"kelson@kiwix.org\", \"verbose\": true }]" "https://farm.openzim.org/api/task/mwoffliner"
```
