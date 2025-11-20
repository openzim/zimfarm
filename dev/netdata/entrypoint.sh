#!/bin/bash

# setup custom hostname for node in netdata
if [ ! -z "${NETDATA_HOSTNAME}" ]
then
    printf "\n hostname = ${NETDATA_HOSTNAME}\n" >> /etc/netdata/netdata.conf
fi

# Define the netdata user
DOCKER_USR="${DOCKER_USR:-netdata}"

# copy of netdata's entrypoint
BALENA_PGID=$(stat -c %g /var/run/balena.sock 2>/dev/null || true)
DOCKER_PGID=$(stat -c %g /var/run/docker.sock 2>/dev/null || true)

re='^[0-9]+$'
if [[ $BALENA_PGID =~ $re ]]; then
  echo "Netdata detected balena-engine.sock"
  DOCKER_HOST='unix:///var/run/balena-engine.sock'
  PGID="$BALENA_PGID"
elif [[ $DOCKER_PGID =~ $re ]]; then
  echo "Netdata detected docker.sock"
  DOCKER_HOST="unix:///var/run/docker.sock"
  PGID="$DOCKER_PGID"
fi
export PGID
export DOCKER_HOST

if [ -n "${PGID}" ]; then
  echo "Creating docker group ${PGID}"
  addgroup --gid "${PGID}" "docker" 2>/dev/null || echo >&2 "Could not add group docker with ID ${PGID}, its already there probably"
  echo "Assign netdata user to docker group ${PGID}"
  usermod -a -G "docker" "${DOCKER_USR}" 2>/dev/null || echo >&2 "Could not add netdata user to group docker with ID ${PGID}"
fi

if mountpoint -q /etc/netdata && [ -z "$(ls -A /etc/netdata)" ]; then
  echo "Copying stock configuration to /etc/netdata"
  cp -a /etc/netdata.stock/. /etc/netdata
fi

# Run update-stream-whitelist on startup
echo "Running initial stream whitelist update"
/usr/local/bin/update-stream-whitelist.sh &

# Start cron in the background
echo "Starting cron daemon"
cron

# Start netdata in the foreground
echo "Starting netdata"
exec /usr/sbin/netdata -u "${DOCKER_USR}" -D -s /host -p "${NETDATA_LISTENER_PORT}"
