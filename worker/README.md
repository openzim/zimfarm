# Overview

Zimfarm worker is a celery node that generate zim files based on  dispatcher instructions.

After successfully established a secure connection with dispatcher, worker will receive and execute tasks to generate zim files. 
Each task contains roughly three stages:

- prepare: run helper docker containers, pull images, etc
- generate: generate zim files using a offliner docker container
- upload: upload the zim files back to zimfarm warehouse

To run containers, zimfarm worker need to have access to a docker socket on the host system.

## Requirements:

Any Linux or Unix based system that has docker installed. Windows are not supported.

## Environmental Variables

- USERNAME
- PASSWORD
- WORKING_DIR: path of a working directory in host system
- NODE_NAME: name of the celery node
- QUEUES: comma separated queue names
  - offliner_default
  - offliner_small
  - offliner_medium 
  - offliner_large  

## Docker Volumes

- docker socket `/var/run/docker.sock:/var/run/docker.sock`
- rsa private key `PATH:/usr/src/.ssh/id_rsa`
- working dir `PATH:/zim_files`

## Example

```bash
docker run \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v PATH_SSH_KEY:/usr/src/.ssh/id_rsa \
    -v PATH_WORKING_DIR:/zim_files \
    --env USERNAME='username' \
    --env PASSWORD='password' \
    --env WORKING_DIR='PATH_WORKING_DIR' \
    --env NODE_NAME='default_node_name' \
    --env QUEUES='offliner_small' \
openzim/zimfarm-worker:latest
```
