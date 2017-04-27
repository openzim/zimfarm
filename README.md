# ZIM Farm
A farm operated by bots to grow and harvest new zim files. There are three main components:

- Dispatcher
- Broker
- Worker

Technology used

- Docker
- Python 3.5, Angular
- Flask, Celery & RabbitMQ
- SQLite

## Stage 1: Simple async task with Docker

Goal: create a system that handles addition of two numbers asynchronously

- one dispatcher, one broker and one local worker
- WebAPI to enqueue a new task and query task status by ID
- run with one `docker-compose` command

### Steps to run

1. make sure docker and docker-compose are installed on your system
2. clone this repo
3. make sure you are in master branch
4. open a terminal session change directory to root of this repo
5. `docker-compose up --build`
6. wait for docker to do its job

### Enqueue a new task

Now, you could try to enqueue a task by sending a request like this: 
```
curl http://localhost:80/task/delayed_add -X POST -H "Content-Type: application/json" -d '{"x":4,"y":10}'
```
If everything is correct, you will be able to get the following response:
```
{
  "task": {
    "id": "252b6354-a06f-426c-8dff-529845e88bf6",
    "name": "delayed_add",
    "status": "PENDING"
  }
}
```

Meanwhile, in terminal, you should be able to see things like this:
```
worker_1      | [2017-04-27 18:08:32,595: INFO/MainProcess] Received task: delayed_add[e926fd8e-d0a7-492b-a566-dde46c91d502]
dispatcher_1  | [pid: 15|app: 0|req: 6/12] 172.18.0.1 () {36 vars in 518 bytes} [Thu Apr 27 18:08:32 2017] POST /task/delayed_add => generated 123 bytes in 6 msecs (HTTP/1.1 200) 2 headers in 72 bytes (2 switches on core 0)
dispatcher_1  | 172.18.0.1 - - [27/Apr/2017:18:08:32 +0000] "POST /task/delayed_add HTTP/1.1" 200 123 "-" "Paw/3.0.16 (Macintosh; OS X/10.12.4) GCDHTTPRequest" "-"
worker_1      | [2017-04-27 18:08:32,743: WARNING/PoolWorker-2] delayed add begins: 4 + 10 = ??
worker_1      | [2017-04-27 18:08:37,749: WARNING/PoolWorker-2] delayed add finished: 4 + 10 = 14
worker_1      | [2017-04-27 18:08:37,751: INFO/PoolWorker-2] Task delayed_add[e926fd8e-d0a7-492b-a566-dde46c91d502] succeeded in 5.008131870999932s: 14
```

### Check task status

At any time, you could query a task's progress using its ID.
```
curl http://localhost:80/task/status/252b6354-a06f-426c-8dff-529845e88bf6
```
You should be able to see the following response:
```
{
  "id": "252b6354-a06f-426c-8dff-529845e88bf6",
  "result": 14,
  "status": "SUCCESS"
}
```
If you are not able to see `SUCCESS`, please give it a few more try. This is a known issue. See below.


### Known Issue

The task query API does not always return the correct result. I am not totally sure why, but I think this is due to the rpc result backend has the restriction of [one queue per client](http://docs.celeryproject.org/en/latest/internals/reference/celery.backends.rpc.html#module-celery.backends.rpc). But in our case, we have 4 queues (4 uWSGI processes). If the uWSGI process handled the status query request is not the same that started the task, celery will not be able to determine the task's status, hence return `PENDING`.

#### How to solve it?
 We could try to use another result backend like SQLite

## Note: Useful commands
- remove all containers: `docker rm $(docker ps -a -q)`
- remova all untagged images `docker rmi $(docker images -a | grep "^<none>" | awk "{print $3}")`