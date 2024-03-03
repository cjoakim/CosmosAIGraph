"""
This module is for ad-hoc tasks not related to the actual working app.
Usage:
    python main.py list_defined_env_vars
    python main.py load_vcore_with_library_documents
    python main.py create_vcore_indexes
    python main.py test_graph_loading_from_container
Options:
  -h --help     Show this screen.
  --version     Show version.
"""

import json
import sys
import time
import os
import psutil
import traceback

from docopt import docopt
from dotenv import load_dotenv

from pysrc.services.config_service import ConfigService
from pysrc.services.cosmos_vcore_service import CosmosVCoreService
from pysrc.util.fs import FS


def print_options(msg):
    print(msg)
    arguments = docopt(__doc__, version="1.0.0")
    print(arguments)


def list_defined_env_vars():
    env_var_names = sorted(ConfigService.defined_environment_variables().keys())
    for name in env_var_names:
        value = ConfigService.envvar(name)
        print("{}: {}".format(name, value))


def connect_to_vcore_graph_source():
    """
    connect to the vcore account, and return a 3-tuple of
    (vcore, dbname, cname), where vcore is an instance of
    class CosmosVCoreService.
    """
    opts = dict()
    opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
    vcore = CosmosVCoreService(opts)
    if "pymongo.mongo_client.MongoClient" in str(type(vcore.get_client())):
        print("connected to vcore")
    else:
        print("unable to connect to vcore; exiting")
        return
    dbname = ConfigService.graph_source_db()
    cname = ConfigService.graph_source_container()
    vcore.set_db(dbname)
    vcore.set_coll(cname)
    return (vcore, dbname, cname)


def load_vcore_with_library_documents():
    vcore, dbname, cname = connect_to_vcore_graph_source()
    print("using vcore db: {}, collection: {}".format(dbname, cname))
    pause_seconds = 10
    print("pausing {} seconds before loading the documents...".format(pause_seconds))
    time.sleep(pause_seconds)
    max_load_idx = 999999
    load_docs_from_directory(vcore, max_load_idx, "../data/npm/wrangled_libs")
    load_docs_from_directory(vcore, max_load_idx, "../data/pypi/wrangled_libs")


def load_docs_from_directory(vcore, max_load_idx, wrangled_libs_dir):
    files_list = FS.list_files_in_dir(wrangled_libs_dir)
    filtered_files_list = filter_files_list(files_list, ".json")
    max_idx = len(filtered_files_list) - 1
    for idx, filename in enumerate(filtered_files_list):
        fq_name = "{}/{}".format(wrangled_libs_dir, filename)
        if fq_name.endswith(".json"):
            if idx < max_load_idx:
                try:
                    print("processing {} of {}: {}".format(idx, max_idx, fq_name))
                    doc = FS.read_json(fq_name)
                    vcore.insert_doc(doc)
                except Exception as e:
                    print("error processing {}: {}".format(fq_name, str(e)))
                    continue


def filter_files_list(files_list, suffix):
    filtered = list()
    for f in files_list:
        if f.endswith(suffix):
            filtered.append(f)
    return filtered


def create_vcore_indexes():
    vcore, dbname, cname = connect_to_vcore_graph_source()
    print("using vcore db: {}, collection: {}".format(dbname, cname))

    indexes = vcore.get_coll_indexes(cname)
    print("indexes before:\n{}".format(json.dumps(indexes, sort_keys=False, indent=2)))

    vcore.create_simple_index("libtype")
    vcore.create_simple_index("name")
    vcore.create_simple_index("id")

    indexes = vcore.get_coll_indexes(cname)
    print("indexes after:\n{}".format(json.dumps(indexes, sort_keys=False, indent=2)))

    # cache container
    cname = "cache"
    vcore.set_db(dbname)
    vcore.set_coll(cname)
    print("using vcore db: {}, collection: {}".format(dbname, cname))
    vcore.create_simple_index("cache_key")
    indexes = vcore.get_coll_indexes(cname)
    print("indexes after:\n{}".format(json.dumps(indexes, sort_keys=False, indent=2)))


def test_graph_loading_from_container():
    """prototype logic for GraphBuilder.load_from_container()"""
    vcore, dbname, cname = connect_to_vcore_graph_source()
    coll = vcore.get_coll()
    docs_read = 0
    t1 = time.perf_counter()
    for libtype in ["npm", "pypi"]:
        query_spec = {"libtype": libtype}
        projection = library_projection_attrs()
        cursor = coll.find(query_spec, projection=projection, skip=0, limit=999999)
        for idx, doc in enumerate(cursor):
            docs_read = docs_read + 1
            if idx % 1000 == 0:
                print("doc: {} {}".format(idx, doc))
    seconds = time.perf_counter() - t1
    print("docs read: {} in {} seconds".format(docs_read, seconds))


def library_projection_attrs():
    """
    The in-memory rdflib graph is built from these few Cosmos DB document attributes.
    See https://pymongo.readthedocs.io/en/stable/api/pymongo/collection.html#pymongo.collection.Collection.find
    """
    return {
        "_id": 0,
        "libtype": 1,
        "id": 1,
        "name": 1,
        "kwds": 1,
        "license_kwds": 1,
        "developers": 1,
        "dependency_ids": 1,
    }


if __name__ == "__main__":
    load_dotenv(override=True)
    if len(sys.argv) < 2:
        print_options("Error: invalid command-line")
        exit(1)
    else:
        try:
            func = sys.argv[1].lower()
            if func == "list_defined_env_vars":
                list_defined_env_vars()
            elif func == "load_vcore_with_library_documents":
                load_vcore_with_library_documents()
            elif func == "create_vcore_indexes":
                create_vcore_indexes()
            elif func == "test_graph_loading_from_container":
                test_graph_loading_from_container()
            else:
                print_options("Error: invalid function: {}".format(func))
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())
