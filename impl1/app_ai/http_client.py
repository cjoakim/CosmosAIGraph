"""
This script is intended for development use to invoke a locally running
instance of app_graph.
Usage:
  python http_client.py <func>
  python http_client.py get <url>
  python http_client.py get http://localhost:8002/
  python http_client.py get http://localhost:8002/liveness
  python http_client.py post_gen_sparql_query_moderation http://localhost:8002/gen_sparql_query
  python http_client.py post_vectorize http://localhost:8002/vectorize
Options:
  -h --help     Show this screen.
  --version     Show version.
"""

import base64
import json
import sys
import time
import os
import textwrap
import traceback
import uuid

import httpx
import jinja2

from docopt import docopt

from pysrc.util.fs import FS


def print_options(msg):
    print(msg)
    arguments = docopt(__doc__, version="1.0.0")
    print(arguments)


def get(url):
    r = httpx.get(url)
    print(r)
    print(r.json())


def post_gen_sparql_query_moderation(url):
    postdata = dict()
    postdata["session_id"] = str(uuid.uuid1())
    postdata["owl"] = "<x></x>"
    postdata["natural_language"] = "this is long enough"
    print(postdata)
    r = httpx.post(url, data=json.dumps(postdata))
    print("----- response text -----")
    print(r.text)
    print("----- pretty-print JSON response object -----")
    obj = json.loads(r.text)
    print(json.dumps(obj, sort_keys=False, indent=2))


def post_vectorize(url):
    postdata = dict()
    postdata["session_id"] = str(uuid.uuid1())
    postdata[
        "text"
    ] = "four score and seven years ago our fathers brought forth on this continent a new nation conceived in liberty and dedicated to the proposition"
    print(postdata)
    r = httpx.post(url, data=json.dumps(postdata))
    print("----- response text -----")
    print(r.text)
    print("----- pretty-print JSON response object -----")
    obj = json.loads(r.text)
    print(json.dumps(obj, sort_keys=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            func = sys.argv[1].lower()
            if func == "get":
                url = sys.argv[2]
                get(url)
            elif func == "post_gen_sparql_query_moderation":
                url = sys.argv[2]
                post_gen_sparql_query_moderation(url)
            elif func == "post_vectorize":
                url = sys.argv[2]
                post_vectorize(url)
            else:
                print_options("Error: invalid function: {}".format(func))
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())
    else:
        print_options("Error: no command-line args provided")
