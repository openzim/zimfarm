# Overview

Zimfarm worker is a celery node that generate zim files based on dispatcher instructions.

After successfully established a secure connection with dispatcher,
worker will receive and execute tasks to generate zim files. Each task
contains roughly three stages:

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

3. Confirm the RSA key has been uploaded successfully

    ```bash
    curl "https://farm.openzim.org/api/users/automactic/keys" \
         -H 'Authorization: Bearer ACCESS_TOKEN'
    ```


## Example

__note__: your local `PATH_WORKING_DIR` must be group writable (chgrp rwx PATH_WORKING_DIR)

```bash
docker run \
    -v /var/run/docker.sock:/var/run/docker.sock:rw \
    -v PATH_SSH_KEY:/usr/src/.ssh/id_rsa:ro \
    -v PATH_WORKING_DIR:/zim_files:rw \
    --env USERNAME='username' \
    --env PASSWORD='password' \
    --env WORKING_DIR='PATH_WORKING_DIR' \
    --env NODE_NAME='default_node_name' \
    --env QUEUES='default' \
    --env CONCURRENCY=2 \
    --name=zimfarm_worker \
openzim/zimfarm-worker:latest
```

## Optimization

Workers (containers and sub-containers) inherits resources limits from the docker daemon which is usually launched as root.

For workers' purposes, it is interesting to have the most available number of files open (`nofile`/`-n`) and the largest `stack`/`-s`).

You can check docker's limits via:

``` sh
cat /proc/$(ps -ef | grep dockerd | head -n 1 |awk '{ print $2 }')/limits
```

Look for `Max stack size` and `Max open files`.

**Note:** On most recent linux distro, the maximum value for _Max open files_ is hardcoded in the kernel and is `1048576` (1,048,576). If you're already getting this value (default on Ubuntu 18.04 server LTS), **there's no need to tweak it**.

### Updating values of `nofile` and `stack`:

* Change System and User values in systemd

``` sh
echo "DefaultLimitNOFILE=1048576" |sudo tee /etc/systemd/system.conf /etc/systemd/user.conf
echo "DefaultLimitSTACK=infinity" |sudo tee /etc/systemd/system.conf /etc/systemd/user.conf
sudo systemctl daemon-reexec
```
* Add overrides to `docker` service definition

``` sh
sudo mkdir -p /etc/systemd/system/docker.service.d/
echo -e "[Service]\nLimitNOFILE=1048576\nLimitSTACK=infinity" |sudo tee /etc/systemd/system/docker.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart docker
```

Verify that new values applied (reboot might help):

``` sh
cat /proc/$(ps -ef | grep dockerd | head -n 1 |awk '{ print $2 }')/limits
```

_Note_: `/etc/security/limits.conf` is not used anymore on systemd-based distro.
