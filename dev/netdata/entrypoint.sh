#!/bin/bash

# setup custom hostname for node in netdata
if [ ! -z "${NETDATA_HOSTNAME}" ]
then
    printf "\n hostname = ${NETDATA_HOSTNAME}\n" >> /etc/netdata/netdata.conf
fi

# copy of netdata's entrypoint
BALENA_PGID=$(stat -c %g /var/run/balena.sock 2>/dev/null || true)
DOCKER_PGID=$(stat -c %g /var/run/docker.sock 2>/dev/null || true)

re='^[0-9]+$'
if [[ $BALENA_PGID =~ $re ]]; then
  echo "Netdata detected balena-engine.sock"
  DOCKER_HOST='/var/run/balena-engine.sock'
  PGID="$BALENA_PGID"
elif [[ $DOCKER_PGID =~ $re ]]; then
  echo "Netdata detected docker.sock"
  DOCKER_HOST="/var/run/docker.sock"
  PGID="$DOCKER_PGID"
fi
export PGID
export DOCKER_HOST

if [ -n "${PGID}" ]; then
  echo "Creating docker group ${PGID}"
  addgroup -g "${PGID}" "docker" || echo >&2 "Could not add group docker with ID ${PGID}, its already there probably"
  echo "Assign netdata user to docker group ${PGID}"
  usermod -a -G "${PGID}" "${DOCKER_USR}" || echo >&2 "Could not add netdata user to group docker with ID ${PGID}"
fi

if mountpoint -q /etc/netdata && [ -z "$(ls -A /etc/netdata)" ]; then
  echo "Copying stock configuration to /etc/netdata"
  cp -a /etc/netdata.stock/. /etc/netdata
fi

# start cron to regen stream config every 15mn
exec crond -f
