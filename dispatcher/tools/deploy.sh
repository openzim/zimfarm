#!/usr/bin/env bash

if [ ! -d "/data/nginx" ]; then
  sudo mkdir -p /data/nginx
  sudo curl https://raw.githubusercontent.com/jwilder/nginx-proxy/master/nginx.tmpl > /data/nginx/nginx.tmpl
fi