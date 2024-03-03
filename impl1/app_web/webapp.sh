#!/bin/bash

# Start the web app, running within the hypercorn server.
# Entry point is webapp.py, 'app' is the FastAPI object.
# hypercorn enables restarting the app as the Python code changes.
# Chris Joakim, Microsoft

mkdir -p tmp

hypercorn webapp:app --bind 127.0.0.1:8000 --reload
