# ZIM Farm
A farm operated by bots to grow and harvest new zim files. User can submit a new zim file generation task through a web interface and a registered worker will run the task and transfer the file back to the dispatcher. 

Zim file gneration could be a time consuming process and the kiwix project gnerate over 3000 of them per month. The goal of this project is to create a distributed system, called zim farm, to simplify and automate zim file generation process. The distributed system has one dispatcher, whose role is to manage tasks and coordinate between workers. A user, presumably with enough privilege, add one or more tasks to the system through the dispatcher. Workers will then come and pick up those tasks, process them and transfer the result (zim files) back to the dispatcher.

### What is used?

Dispatcher:
- proxy: nginx
  - frontend: angular 2, Node.js
  - backend: flask, celery, sqlite, python
- messaging queue: RabbitMQ

Worker:
- python
- docker

### Steps to run

1. make sure docker and docker-compose are installed on your system
2. clone this repo
3. make sure you are in master branch
4. open a terminal session change directory to root of this repo
5. `docker-compose up --build`
6. wait for docker to do its job
7. go to `http://localhost:8080`


### Note: Useful commands
- remove all containers: `docker rm $(docker ps -a -q)`
- remova all untagged images `docker rmi $(docker images -a | grep "^<none>" | awk "{print $3}")`