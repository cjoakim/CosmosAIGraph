"""
Usage:
    python main_nosql.py check_cosmos_config <dbname>
    python main_nosql.py load_libraries_container
    python main_nosql.py load_libraries_container
    python main_nosql.py vector_search_similar_libraries <libname>
    python main_nosql.py vector_search_similar_libraries flask
    python main_nosql.py vector_search_words <word1> <word2> <word3> ...
    python main_nosql.py vector_search_words asynchronous web framework with pydantic
Options:
  -h --help     Show this screen.
  --version     Show version.
"""

# See https://learn.microsoft.com/en-us/azure/postgresql/single-server/connect-python


import asyncio
import json
import sys
import time
import logging
import traceback
import uuid

from docopt import docopt
from dotenv import load_dotenv

from src.services.config_service import ConfigService
from src.services.ai_service import AiService
from src.services.cosmos_nosql_async_service import CosmosNoSQLAsyncService
from src.services.cosmos_nosql_synch_service import CosmosNoSQLSynchService
from src.util.fs import FS


def print_options(msg):
    print(msg)
    arguments = docopt(__doc__, version="1.0.0")
    print(arguments)


async def check_cosmos_config(dbname):
    logging.info("check_cosmos_config, dbname: {}".format(dbname))
    try:
        cname = "libraries"
        nosql_svc = CosmosNoSQLAsyncService()
        await nosql_svc.initialize()

        dbs = await nosql_svc.list_databases()
        logging.info("databases: {}".format(dbs))

        dbproxy = nosql_svc.set_db(dbname)
        print("dbproxy: {}".format(dbproxy))
        #print(str(type(dbproxy)))  # <class 'azure.cosmos.aio._database.DatabaseProxy'>

        containers = await nosql_svc.list_containers()
        print("containers: {}".format(containers))

        ctrproxy = nosql_svc.set_container(cname)
        print("ctrproxy: {}".format(ctrproxy))
        #print(str(type(ctrproxy)))  # <class 'azure.cosmos.aio._container.ContainerProxy'>

        cname = "test"
        ctrproxy = nosql_svc.set_container(cname)
        print("ctrproxy: {}".format(ctrproxy))

        id = str(uuid.uuid4())
        pk = "test"

        doc = await nosql_svc.upsert_item({"id": id, "pk": pk, "name": "test"})
        print("upsert_item doc: {}".format(doc))

        doc = await nosql_svc.point_read(id, pk)
        print("point_read doc: {}".format(doc))

        doc["name"] = "updated"
        updated = await nosql_svc.upsert_item(doc)
        print("updated doc: {}".format(updated))

        response = await nosql_svc.delete_item(id, pk)
        print("delete_item response: {}".format(response))

        try:
            doc = await nosql_svc.point_read(id, pk)
            print("point_read of deleted doc: {}".format(doc))
        except Exception as e:
            print("point_read of deleted doc threw an exception: {}".format(str(e)))

        # nosql_svc.set_db(dbname)
        # ctrs = nosql_svc.list_containers()
        # logging.info("containers: {}".format(ctrs))
    except Exception as e:
        logging.info(str(e))
        logging.info(traceback.format_exc())
    await nosql_svc.close()
    logging.info("end of check_cosmos_config")

def check_cosmos_config_synch(dbname):
    logging.info("check_cosmos_config_synch, dbname: {}".format(dbname))
    try:
        nosql_svc = CosmosNoSQLSynchService()
        dbs = nosql_svc.list_databases()
        logging.info("databases: {}".format(dbs))
        nosql_svc.set_db(dbname)
        ctrs = nosql_svc.list_containers()
        logging.info("containers: {}".format(ctrs))
    except Exception as e:
        logging.info(str(e))
        logging.info(traceback.format_exc())
    #nosql_svc.close()

def load_libraries_container(envname, dbname):
    logging.info(
        "load_libraries_container, envname: {} dbname: {}".format(envname, dbname)
    )
    try:
        nosql_svc = CosmosNoSQLSynchService()
        load_docs_from_directory(nosql_svc, "../data/pypi/wrangled_libs")
    except Exception as e:
        logging.info(str(e))
        logging.info(traceback.format_exc())
    #nosql_svc.close()


def load_docs_from_directory(nosql_svc, wrangled_libs_dir):
    files_list = FS.list_files_in_dir(wrangled_libs_dir)
    filtered_files_list = filter_files_list(files_list, ".json")
    max_idx = len(filtered_files_list) - 1

    for idx, filename in enumerate(filtered_files_list):
        fq_name = "{}/{}".format(wrangled_libs_dir, filename)
        if fq_name.endswith(".json"):
            try:
                if idx < 999999:
                    logging.info(
                        "processing {} of {}: {}".format(idx, max_idx, fq_name)
                    )
                    doc = FS.read_json(fq_name)
                    nosql_svc.upsert_doc(doc)
            except Exception as e:
                logging.info("error processing {}: {}".format(fq_name, str(e)))
                logging.info(traceback.format_exc())
                return


def filter_files_list(files_list, suffix):
    filtered = list()
    for f in files_list:
        if f.endswith(suffix):
            filtered.append(f)
    return filtered


def vector_search_similar_libraries(libname):
    logging.info("vector_search_similar_libraries, libname: {}".format(libname))
    logging.info("TODO - implement")


def vector_search_words(natural_language):
    logging.info("vector_search_words, nl: {}".format(natural_language))
    logging.info("TODO - implement")


if __name__ == "__main__":
    # standard initialization of env and logger
    load_dotenv(override=True)
    logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
    if len(sys.argv) < 2:
        print_options("Error: invalid command-line")
        exit(1)
    else:
        try:
            func = sys.argv[1].lower()
            if func == "check_cosmos_config":
                dbname = sys.argv[2]
                asyncio.run(check_cosmos_config(dbname))
            elif func == "load_libraries_container":
                envname = sys.argv[2]
                dbname  = sys.argv[3]
                load_libraries_container(envname, dbname)
            elif func == "vector_search_similar_libraries":
                libname = sys.argv[2]
                vector_search_similar_libraries(libname)
            elif func == "vector_search_words":
                words = list()
                for idx, arg in enumerate(sys.argv):
                    if idx > 1:
                        words.append(sys.argv[idx])
                natural_language = " ".join(words).strip()
                vector_search_words(natural_language)
            else:
                print_options("Error: invalid function: {}".format(func))
        except Exception as e:
            logging.info(str(e))
            logging.info(traceback.format_exc())
