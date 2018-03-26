#!/usr/bin/env bash

rm -r dist
python setup.py sdist bdist_wheel --universal
twine upload --repository pypitest dist/*
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple --upgrade --no-deps --no-cache --force-reinstall zimfarm-worker