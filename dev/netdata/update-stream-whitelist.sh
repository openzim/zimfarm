#!/bin/sh

STREAMCONFPATH=/etc/netdata/stream.conf

function md5of {
    md5sum $1 | cut -d " " -f 1
}

echo "Updating stream configuration"
regen-stream-conf > $STREAMCONFPATH.new

if [ ! "$(md5of $STREAMCONFPATH)" = "$(md5of $STREAMCONFPATH.new)" ]; then
    echo "workers keys updated. restarting netdata"
    mv $STREAMCONFPATH.new $STREAMCONFPATH
    killall netdata || true
    sleep 5
    /usr/sbin/netdata -u "${DOCKER_USR}" -D -s /host -p "${NETDATA_LISTENER_PORT}" &
else
    rm -f $STREAMCONFPATH.new
    echo "workers keys unchanged"
fi
