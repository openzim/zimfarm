# ZIM Farm
A farm operated by bots to grow and harvest new zim files. User can submit a new zim file generate task through the website and a registered worker will run the task and upload the file back to the dispatcher. There are three main components:

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

### Steps to run

1. make sure docker and docker-compose are installed on your system
2. clone this repo
3. make sure you are in master branch
4. open a terminal session change directory to root of this repo
5. `docker-compose up --build`
6. wait for docker to do its job
7. go to `http://localhost:8080`


## Note: Useful commands
- remove all containers: `docker rm $(docker ps -a -q)`
- remova all untagged images `docker rmi $(docker images -a | grep "^<none>" | awk "{print $3}")`