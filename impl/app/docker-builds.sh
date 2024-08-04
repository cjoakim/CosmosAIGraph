#!/bin/bash

# Build the two microservice Docker images for this app.
# Note 1: be sure to have Docker Desktop running on your system.
# Note 2: please change the Docker image names (the cjoakim prefix).
# Chris Joakim, Microsoft

echo 'building caig_graph image ...'
docker build -f docker/Dockerfile_graph -t cjoakim/caig_graph .

'building caig_web image ...'
docker build -f docker/Dockerfile_web -t cjoakim/caig_web .

echo 'next steps:'
echo '  docker push cjoakim/caig_graph:latest'
echo '  docker push cjoakim/caig_web:latest'

echo 'done'
