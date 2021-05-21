#!/bin/sh

for secret in s3_url zimfarm_username zimfarm_password
do

    if [ -f /run/secrets/$secret ]
    then
        varname=$(echo $secret | tr a-z A-Z)
        echo "[entrypoint] exposing ${secret} secret as ${varname}"
        export $varname=$(cat /run/secrets/$secret)
    fi
done

exec "$@"
