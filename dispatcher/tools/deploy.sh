#!/usr/bin/env bash

if [ ! -d "/data/nginx" ]; then
  mkdir -p /data/nginx
  curl https://raw.githubusercontent.com/jwilder/nginx-proxy/master/nginx.tmpl > /data/nginx/nginx.tmpl
fi