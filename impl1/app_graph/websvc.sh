#!/bin/bash

# Start the web service, running within the hypercorn server.
# Entry point is websvc.py, 'app' is the FastAPI object.
# hypercorn enables restarting the app as the Python code changes.
# Chris Joakim, Microsoft

mkdir -p tmp
mkdir -p uploads

hypercorn websvc:app --bind 127.0.0.1:8001 --reload
