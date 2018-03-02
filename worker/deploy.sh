#!/usr/bin/env bash

rm -r dist
python setup.py sdist bdist_wheel --universal
twine upload --repository pypi dist/*