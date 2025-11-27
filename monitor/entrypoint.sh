#!/bin/bash

# set streaming destination
# shellcheck disable=SC2162
read -d '' STREAM_CONF << EOF
[stream]
 enabled = yes
 destination = ${MONITORING_DEST}
 api key = ${MONITORING_KEY}
 send charts matching = cgroup_zimscraper* cgroup_zimtask*
EOF
echo "${STREAM_CONF}" > /etc/netdata/stream.conf

# configure redis module to scraper (even if there's no redis there)
# shellcheck disable=SC2162
read -d '' REDIS_CONF << EOF
autodetection_retry: 30
jobs:
 - name: scraper
   address: 'redis://${SCRAPER_CONTAINER}:6379'
EOF
echo "${REDIS_CONF}" > /etc/netdata/go.d/redis.conf

# setup custom hostname for node in netdata
if [ -n "${NETDATA_HOSTNAME}" ]
then
    printf "\n hostname = %s" "${NETDATA_HOSTNAME}" >> /etc/netdata/netdata.conf
fi

# netdata's entrypoint
/usr/sbin/run.sh
