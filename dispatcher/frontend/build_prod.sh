#!/usr/bin/env bash

rm -r ./../backend/static/angular/
ng build --prod
mv ./dist ./../backend/static/angular