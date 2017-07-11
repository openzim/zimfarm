# ZIM Farm

The ZIM farm (zimfarm) is a half-decentralised software solution to
build ZIM files (http://www.openzim.org/) efficiently. This means scrapping Web contents,
packaging them into a ZIM file and uploading the result to an online
ZIM files repository.

## Principle

The whole zimfarm system works as a task scheduler and is made of two
kinds of:

* The '''dispatcher''', the central node which takes and dispatches
  tasks. It is thought to be managed by the openZIM project admin and
  put somewhere online on the Internet.

* The '''workers''' which execute tasks. They are thought to be run by
  openZIM volunteers in different places available through Internet.

To get a new ZIM file the typical workflow is:
1 User submits a new task (to get a specific ZIM file made).
2 Dispatcher queues the task.
3 A worker pulls the task.
4 Worker make the ZIM file an dupload it.

## Run the system as a whole

1 Make sure docker and docker-compose are installed on your system
2 Clone this repo
3 <ake sure you are in master branch
4 Open a terminal session change directory to root of this repo
5 Run `docker-compose up --build`
6 Wait for docker to do its job
7 Go to `http://localhost:8080` with your Web browser

## Howto
- remove all containers: `docker rm $(docker ps -a -q)`
- remova all untagged images `docker rmi $(docker images -a | grep "^<none>" | awk "{print $3}")`

## Architecture

The whole system is build by reusing the best of free software
libraries components. The whole ZIM farm solutioon itself is made
available using Docker images.

Actually, we use even more Docker images, as the ZIM file are produced
in dedicated custom Docker images the worker has to "invoke" depending
of the properties of the task he has to accomplish.

## Softwares

### Dispatcher

- proxy: nginx
  - frontend: angular 2, Node.js
  - backend: flask, celery, sqlite, python
- message queue: RabbitMQ
- result backend: Redis (may no longer need)

### Worker

- node.js + python
  - mwoffliner
  - celery
