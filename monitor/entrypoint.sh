#!/bin/bash

# set streaming destination
read -d '' STREAM_CONF << EOF
[stream]
 enabled = yes
 destination = ${MONITORING_DEST}
 api key = ${MONITORING_KEY}
EOF
echo "${STREAM_CONF}" > /etc/netdata/stream.conf

# configure redis module to scraper (even if there's no redis there)
read -d '' REDIS_CONF << EOF
jobs:
 - name: scraper
   address: 'redis://${SCRAPER_CONTAINER}:6379'
EOF
echo "${STREAM_CONF}" > /etc/netdata/go.d/redis.conf

# setup custom hostname for node in netdata
if [ ! -z "${NETDATA_HOSTNAME}" ]
then
    printf "\n hostname = ${NETDATA_HOSTNAME}" >> /etc/netdata/netdata.conf
fi

# netdata's entrypoint
/usr/sbin/run.sh
