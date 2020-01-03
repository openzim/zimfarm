zimfarm workers
===

# Run a worker

Running a working means running the `worker-manager` which itself fires `task-worker` containers to handle the tasks.

## Requirements

* A zimfarm user account (with appropriate `worker` role)
* An RSA private key
* Public key uploaded to user account

``` bash
# generate an RSA key pair (use empty passphrase)
ssh-keygen -t rsa -f zimfarm_key
# display its public key (you'll upload it right after)
cat zimfarm_key.pub | cut -d " " -f 2
# upload the public key, giving it a name. token can be copied from the Zimfarm UI
curl -X POST https://api.farm.openzim.org/v1/users/<username>/keys \
    -H 'Authorization: Bearer <token>' \
    -H 'Content-Type: application/json; charset=utf-8' \
    -d $'{"name": "<key-name>", "key": "<key-content>"}'
```

## Sample startup script

``` bash
#!/usr/bin/env bash

ZIMFARM_USERNAME="unknown"
ZIMFARM_WORKER_NAME="unknown"
ZIMFARM_DEBUG=1
ZIMFARM_MAX_RAM="2G"
ZIMFARM_DISK="10G"
ZIMFARM_CPU="3"
ZIMFARM_ROOT=/tmp
ZIMFARM_OFFLINERS="mwoffliner,phet,gutenberg,youtube"

parentdir=$(dirname "$(readlink -f "$0")")
source $parentdir/config.sh || true
datadir=$ZIMFARM_ROOT/data

cont_name="zimfarm_worker-manager"
echo "Stopping $cont_name"
docker stop $cont_name || true
docker rm $cont_name || true

echo "Starting $cont_name"
docker pull openzim/zimfarm-worker-manager:latest
docker run \
    --name $cont_name \
    --restart=always \
    --detach \
    --log-driver json-file \
    --log-opt max-size="100m" \
	-v $datadir:/data \
	-v /var/run/docker.sock:/var/run/docker.sock:ro \
	-v $ZIMFARM_ROOT/id_rsa:/etc/ssh/keys/zimfarm:ro \
	--env ZIMFARM_MEMORY=$ZIMFARM_MAX_RAM \
	--env ZIMFARM_DISK=$ZIMFARM_DISK \
    --env ZIMFARM_CPUS=$ZIMFARM_CPU \
	--env USERNAME=$ZIMFARM_USERNAME \
	--env DEBUG=$ZIMFARM_DEBUG \
	--env WORKER_NAME=$ZIMFARM_WORKER_NAME \
	--env SOCKET_URI="tcp://tcp.farm.openzim.org:32029" \
	--env WEB_API_URI="https://api.farm.openzim.org/v1" \
	--env UPLOAD_URI="sftp://warehouse.farm.openzim.org:1522" \
	--env USE_PUBLIC_DNS="yes" \
	--env OFFLINERS=$ZIMFARM_OFFLINERS \
openzim/zimfarm-worker-manager:latest worker-manager

```

## Helper scripts

### `zimfarm.ps`

``` sh
#!/bin/sh

docker ps --format 'table {{.ID}}\t{{.Label "tid"}}\t{{.Label "schedule_name"}}\t{{.Label "task_id"}}\t{{.RunningFor}}\t{{.Names}}'
```

### `zimfarm.prune`

``` sh
#!/bin/sh

docker system prune --volumes -af
```
