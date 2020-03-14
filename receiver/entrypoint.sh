#!/bin/bash

# Dump environment variables to /etc/environ.json
JSON_PATH=/etc/environ.json
echo "Dump ZIMFARM_* environ variables to $JSON_PATH"

json_output="{\n"
for envLine in $(env)
do
    if [ "$(echo "$envLine" | cut -c1-8)" = "ZIMFARM_" ]; then
        ns=$(echo "$envLine" | sed 's/=/": "/')
        json_output="$json_output    \"$ns\",\n"
    fi
done
json_output=${json_output::-3}  # remove last command and CR
json_output="$json_output\n}\n"
# shellcheck disable=SC2039
echo -e "$json_output" > $JSON_PATH

cat $JSON_PATH

# Start openssh-server
/etc/init.d/ssh start

# Create cron entry for ZIM quarantine
echo "* *  * * *  root  /usr/bin/flock -w 0 /dev/shm/cron.lock /usr/local/bin/check_zims.sh $ZIM_SRC_DIR $ZIM_DST_DIR $ZIM_QUAR_DIR $VALIDATION_LOG_DIR \"$ZIMCHECK_OPTION\" $VALIDATION_OPTION >> /dev/shm/check_zims.log 2>&1" >> /etc/cron.d/check_zims
chmod +x /etc/cron.d/check_zims

exec "$@"
