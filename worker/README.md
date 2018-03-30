# Worker

Worker is a celery node that produce zim files per dispatcher instructions.

After worker successfully established a secure connection with dispatcher, it will start to receive and execute tasks. Each task contains roughly three stages:

- prepare: run helper docker containers, pull images, etc
- generate: generate zim files using a offliner docker container
- upload: upload the zim files back to zimfarm warehouse

To run containers, zimfarm worker need to take control of a docker socket.

## Requirements:

Any Linux or Unix based system that has docker installed. Windows are not supported.

## How to use:

### Method1: docker

1. clone this repo
2. `cd worker`
3. build image: `docker build . -t zimfarm_worker`
4. run container:

```
docker run \
    -d \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v HOST_OUTPUT:/files \
    -e USERNAME=username \
    -e PASSWORD=password \
    -e WORKING_DIR=HOST_OUTPUT \
    zimfarm_worker
```

**Important**: HOST_OUTPUT is where you want the output dir to be on your host system. An absolute path is needed. It appears twice in the above command and you have to use exactly the same value in both places.

Other available environmental variables:

- DISPATCHER_HOST: default farm.openzim.org
- WAREHOUSE_HOST: default farm.openzim.org
- RABBITMQ_PORT: default 5671, port used to communicate with RabbitMQ
- WAREHOUSE_COMMAND_PORT, default 21, warehouse ftp server command port
- WORKING_DIR: working directory in host file system
- REDIS_NAME: default zimfarm_redis, name of redis helper container

### Method2: pip

1. setup virtualenv (optional)
2. `pip install zimfarm-worker`
3. run `zimfarm-worker`, enter your credentials and answer some questions
