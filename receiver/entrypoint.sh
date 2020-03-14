#!/bin/bash

# dump environment variables to /etc/environ.json
JSON_PATH=/etc/environ.json
echo "dump ZIMFARM_* environ variables to $JSON_PATH"

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

# start openssh-server
/etc/init.d/ssh start

# configure zimValidation
echo "* *  * * *  root  /usr/bin/flock -w 0 /dev/shm/cron.lock find $ZIM_SRC_DIR -iname \"*.zim\" -exec bash /usr/local/bin/check_zim.sh \"{}\" $ZIM_SRC_DIR $ZIM_DST_DIR $ZIM_QUAR_DIR $VALIDATION_LOG_DIR \"$ZIMCHECK_OPTION\" $VALIDATION_OPTION ';' >> /dev/shm/check_zim.log 2>&1" >> /etc/cron.d/zimvalidation

exec "$@"
