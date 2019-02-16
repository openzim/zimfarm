# Overview

Zimfarm worker is a celery node that generate zim files based on dispatcher instructions.

After successfully established a secure connection with dispatcher, 
worker will receive and execute tasks to generate zim files. 
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
- CONCURRENCY: max number of concurrent tasks, default to number of CPU cores
- QUEUES: comma separated queue names
  - default
  - small
  - medium 
  - large  

## Docker Volumes

- docker socket `/var/run/docker.sock:/var/run/docker.sock`
- rsa private key `PATH:/usr/src/.ssh/id_rsa`
- working dir `PATH:/zim_files`

## Upload Your RSA Key

Zimfarm worker use sftp and public key authentication to transfer generated zim files to warehouse.
Please make sure the RSA public key is uploaded to dispatcher using the public API before starting a worker.

1. Get access token

    ```bash
    curl -X "POST" "https://farm.openzim.org/api/auth/oauth2" \
         -H 'Content-Type: application/x-www-form-urlencoded; charset=utf-8' \
         --data-urlencode "grant_type=password" \
         --data-urlencode "username=USERNAME" \
         --data-urlencode "password=PASSWORD"
    ```

    The access token is in the `access_token` field of the response json.

2. Upload RSA public key

    ```bash
    curl -X "POST" "https://farm.openzim.org/api/users/kelson/keys" \
         -H 'Authorization: Bearer ACCESS_TOKEN' \
         -H 'Content-Type: application/json; charset=utf-8' \
         -d $'{"name": "WORKER_NAME", "key": "AAAAB3NzaC1y......BerDXG7kL"}'
    ```
    
    Please only include the content of the RSA key in the request body.
    
3. Confirm the ssk key has been uploaded successfully
    
    ```bash
    curl "https://farm.openzim.org/api/users/automactic/keys" \
         -H 'Authorization: Bearer ACCESS_TOKEN'
    ```


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
    --env QUEUES='default' \
    --env CONCURRENCY=2 \
    --name=zimfarm_worker \
openzim/zimfarm-worker:latest
```
