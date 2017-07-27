#!/bin/sh

useradd zimfarm_worker
usermod -a -G staff zimfarm_worker

python3 app/main.py