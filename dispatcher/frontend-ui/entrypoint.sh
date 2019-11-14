#!/bin/bash

JS_PATH=/usr/share/nginx/html/environ.js
echo "dump ZIMFARM_* environ variables to $JS_PATH"

json_output="environ = {\n"
envs_output=$(env)
envLines=(${envs_output/\\n/ })
for envLine in "${envLines[@]}"; do
	lineElems=(${envLine/=/ })
	key=${lineElems[0]}
	if [[ "$key" =~ ^ZIMFARM_.+$ ]]; then
		json_output+="    \"$key\": \"${lineElems[1]}\",\n"
	fi
done
json_output+="}\n"
echo -e $json_output > $JS_PATH

cat $JS_PATH
echo "-----"

exec "$@"
