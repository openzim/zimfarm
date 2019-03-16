#!/usr/bin/env bash

echo "Stopping zimfarm_worker"
docker stop zimfarm_worker || true
docker rm zimfarm_worker || true

echo "Stopping offliners"
docker stop $(docker ps -aq -f=zimfarm_)
docker rm $(docker ps -aq -f=zimfarm_)
rm -r /srv/zimfarm

echo "Starting zimfarm_worker"
docker pull openzim/zimfarm-worker:latest &&
docker run \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /home/automactic/.ssh/id_rsa:/usr/src/.ssh/id_rsa \
    -v /srv/zimfarm:/zim_files \
    --env USERNAME='automactic' \
    --env PASSWORD='macOS10&open' \
    --env WORKING_DIR='/srv/zimfarm' \
    --env NODE_NAME='mwoffliner1.mwoffliner.eqiad.wmflabs' \
    --env QUEUES='small,medium' \
    --env CONCURRENCY=5 \
    --name=zimfarm_worker -d \
openzim/zimfarm-worker:latest