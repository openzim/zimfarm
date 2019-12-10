#!/bin/sh

JS_PATH=/usr/share/nginx/html/environ.js
echo "dump ZIMFARM_* environ variables to $JS_PATH"

json_output="var environ = {\n"
envs_output=$(env)
# shellcheck disable=SC2039
envLines=${envs_output//;/$'\n'}
for envLine in $envLines
do
    if [ "$(echo "$envLine" | cut -c0-8)" = "ZIMFARM_" ]; then
        ns=$(echo "$envLine" | sed 's/=/": "/')
        json_output="$json_output    \"$ns\",\n"
    fi
done
json_output="$json_output}\n"
# shellcheck disable=SC2039
echo -e "$json_output" > $JS_PATH

cat $JS_PATH
echo "-----"

exec "$@"
