#!/bin/bash

mkdir -p tmp

source bin/activate

echo 'executing unit tests with code coverage ...'
pytest -v --cov=pysrc/ --cov-report html tests/
