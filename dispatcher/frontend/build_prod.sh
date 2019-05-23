#!/usr/bin/env bash

rm -r ./../backend/static/angular/
# replace entities placeholder with backend values
python ./gen_entities-ts.py
ng build --prod
mv ./dist ./../backend/static/angular
# offer to checkout entities placeholder
read -t 10 -p "Do you want to run git checkout on the entities placeholder? [Y/N]" answer
if [ "$answer" != "${answer#[Yy]}" ] ;then
    git checkout src/app/services/entities.ts
fi
