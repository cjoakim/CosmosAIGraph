# This script executes the complete set of unit tests
# for the app_common package, with code coverage.
# Note: The Graph microservice should be running on localhost
# when these tests are executed.
# Chris Joakim, Microsoft

New-Item -ItemType Directory -Force -Path .\tmp | out-null
del tmp/*.*

echo 'executing unit tests with code coverage ...'
pytest -v --cov=src/ --cov-report html tests/
