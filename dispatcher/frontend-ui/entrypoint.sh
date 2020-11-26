#!/bin/sh

JS_PATH=/usr/share/nginx/html/environ.json
echo "dump ZIM* environ variables to $JS_PATH"

python -c 'import os; import json; print(json.dumps({k: v for k, v in os.environ.items() if k.startswith("ZIMFARM_")}, indent=4))' > $JS_PATH

cat $JS_PATH
echo "-----"

exec "$@"
