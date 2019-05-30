#!/bin/sh
# checks GID of docker socket on host then change container's docker gid to match it
# once done, replace pid with worker app

set -x

# configure script to call original entrypoint
set python app/main.py "$@"

# GID might have been set on host to match container's GID
if [ "$(id -u)" = "0" ]; then
  # get gid of docker socket file
  SOCK_DOCKER_GID=`ls -ng /var/run/docker.sock | cut -f3 -d' '`

  # get group of docker inside container
  CUR_DOCKER_GID=`getent group docker | cut -f3 -d: || true`

  # if they don't match, adjust
  if [ ! -z "$SOCK_DOCKER_GID" -a "$SOCK_DOCKER_GID" != "$CUR_DOCKER_GID" ]; then
    groupmod -g ${SOCK_DOCKER_GID} -o docker
  fi
  if ! groups celery_runner | grep -q docker; then
    usermod -aG docker celery_runner
  fi
fi

# replace the current pid 1 with original entrypoint
exec "$@"
