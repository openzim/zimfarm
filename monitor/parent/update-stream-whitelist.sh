#!/bin/bash

STREAMCONFPATH=/etc/netdata/stream.conf

function md5of {
    md5sum "$1" | cut -d " " -f 1
}

echo "Updating stream configuration"

# Run regen-stream-conf and capture exit code
if ! /usr/local/bin/regen-stream-conf > $STREAMCONFPATH.new; then
    echo "ERROR: regen-stream-conf failed, keeping existing configuration"
    rm -f $STREAMCONFPATH.new
    exit 1
fi

# Check if the output file is empty or too small (probable error)
if [ ! -s "$STREAMCONFPATH.new" ]; then
    echo "ERROR: regen-stream-conf produced empty output, keeping existing configuration"
    rm -f $STREAMCONFPATH.new
    exit 1
fi

if [ ! -f "$STREAMCONFPATH" ]; then
    echo "No stream.conf exists, installing fresh"
    mv "$STREAMCONFPATH.new" "$STREAMCONFPATH"
    exit 0
fi


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
