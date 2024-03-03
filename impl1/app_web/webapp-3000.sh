#!/bin/bash

# Start the web app on alternative port 3000, instead of port 8000.
# This allows the microservices to be executed with 'docker compose' but have an
# alternative in-development version of the webapp running on port 3000.
# Chris Joakim, Microsoft

mkdir -p tmp

hypercorn webapp:app --bind 127.0.0.1:3000 --reload
