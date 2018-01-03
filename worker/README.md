# Zimfarm Worker

The celery worker produces zim files with the following workflow:

1. receive zim file generation instruction from dispatcher
2. generate zim file
3. upload zim file to the warehouse

**Important**: It is required to bind host's docker socket to worker container,
since worker will generate zim files using offliner containers (like mwoffliner).
Thus, it is essential not to quit any container on your host system started by worker.

## How to run

1. clone this repo
2. change directory to worker: `cd worker`
3. set username, password and other environment variables in the `.env`
   file, see guide in section below
4. build the docker image: `docker build -t zimfarm_worker .`
5. run the container with the following command:
```
docker run -v /var/run/docker.sock:/var/run/docker.sock \
           -v HOST_WORKING_DIR:CONTAINER_WORKING_DIR \
           --env-file .env
           zimfarm_worker
```

Example:
```
docker build -t zimfarm_worker . &&
docker run -v /var/run/docker.sock:/var/run/docker.sock \
           -v /Volumes/Data/ZimFiles:/ZimFiles \
           --env-file .env \
           zimfarm_worker
```

## Environment Variables

### Required:

| Name                   | Description                                                                |
|------------------------|----------------------------------------------------------------------------|
| USERNAME               | your username at Zimfarm                                                   |
| PASSWORD               | your password at Zimfarm                                                   |
| DISPATCHER_HOST        | host of Zimfarm dispatcher                                                 |
| WAREHOUSE_HOST         | host of Zimfarm warehouse                                                  |
| RABBITMQ_PORT          | port of RabbitMQ port on dispatcher, used for worker coordination          |
| WAREHOUSE_COMMAND_PORT | command port of warehouse ftp server                                       |
| HOST_WORKING_DIR       | directory for offliner containers to generate zim files in the host system |
| CONTAINER_WORKING_DIR  | path where HOST_WORKING_DIR is mapped to inside the container              |

### Optional:

- **REDIS_NAME**: name of redis container used by offliners.
If multiple offliners all require a redis container,
there will only be one created and all offliners will share it.

- **CONCURRENCY**: number of offliners to run at the same time,
greater than or equals to one, default 2.
