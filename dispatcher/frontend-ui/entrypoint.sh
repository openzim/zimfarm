#!/bin/sh

if [ -z "${ENVIRON_PATH}" ]
then
    ENVIRON_PATH=/usr/share/nginx/html/environ.json
fi
echo "dump ZIMFARM_* environ variables to $ENVIRON_PATH"

python3 -c 'import os; import json; print(json.dumps({k: v for k, v in os.environ.items() if k.startswith("ZIMFARM_")}, indent=4))' > $ENVIRON_PATH

cat $ENVIRON_PATH
echo "-----"

exec "$@"
