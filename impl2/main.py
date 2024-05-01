"""
This module is for ad-hoc tasks not related to the actual working app.
Usage:
    python main.py display_caig_env_vars
    python main.py create_vcore_collections_and_indexes
    python main.py load_vcore
    python main.py load_graph_from_vcore
    python main.py load_graph_from_vcore --queries
    python main.py build_az_cli_env_vars
Options:
  -h --help     Show this screen.
  --version     Show version.
"""

import json
import os
import sys
import time
import logging
import traceback
import uuid

from docopt import docopt
from dotenv import load_dotenv

from pymongo import InsertOne

import rdflib

from rdflib import Graph, Literal, RDF, URIRef, BNode
from rdflib.namespace import Namespace, NamespaceManager
from rdflib.extras.infixowl import AllClasses, AllProperties, GetIdentifiedClasses

from pysrc.models.rdf_query_result import RdfQueryResult
from pysrc.services.config_service import ConfigService
from pysrc.services.cosmos_vcore import CosmosVCore
from pysrc.services.imdb_graph_service import ImdbGraphService
from pysrc.util.fs import FS

# Inclusion/Exclusion Parameters and Filenames:
TITLES_FILE = "data/titles.json"
NAMES_FILTERED_FILE = "data/names_filtered.json"

def print_options(msg):
    print(msg)
    arguments = docopt(__doc__, version="1.0.0")
    print(arguments)


def display_caig_env_vars():
    """ display the environment variables that begin with CAIG_ """
    names = os.environ.keys()
    selected_names = list()
    for name in names:
        if name.startswith("CAIG_"):
            selected_names.append(name)
    for name in sorted(selected_names):
        val = os.environ[name]
        print("{} -> {}".format(name, val))

def connect_to_vcore_graph_source():
    """
    connect to the vcore account, and return a 3-tuple of
    (vcore, dbname, cname), where vcore is an instance of
    class CosmosVCore.
    """
    opts = dict()
    opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
    vcore = CosmosVCore(opts)
    if "pymongo.mongo_client.MongoClient" in str(type(vcore.get_client())):
        logging.info("connected to vcore")
    else:
        logging.info("unable to connect to vcore; exiting")
        return
    dbname = ConfigService.graph_source_db()
    cname = "imdb" # ConfigService.graph_source_container()
    vcore.set_db(dbname)
    vcore.set_coll(cname)
    return (vcore, dbname, cname)


def load_vcore():
    """
    Load the Cosmos DB vCore imdb container with the names/people and titles/movies.
    First delete all documents in the container, then bulk load it in batches of 100.
    """
    vcore, dbname, cname = connect_to_vcore_graph_source()
    logging.info("using vcore db: {}, collection: {}".format(dbname, cname))
    pause_seconds = 10
    logging.info(
        "pausing {} seconds before deleting then loading the documents...".format(pause_seconds)
    )
    time.sleep(pause_seconds)
    max_load_idx = 999999

    # delete the current documents in the 'imdb' container
    result = vcore.delete_many({})
    print(result)

    # See https://pymongo.readthedocs.io/en/stable/examples/bulk.html

    # read the NAMES_FILTERED_FILE, load to the 'imdb' container
    t1 = time.perf_counter()
    names = load_names_filtered()
    operations = list()
    batch_num = 0
    doc_count = 0
    for idx, nconst in enumerate(sorted(names.keys())):
        if idx < max_load_idx:
            try:
                p = names[nconst]
                p["_id"] = str(uuid.uuid4())
                p["doctype"] = "person"
                operations.append(InsertOne(p))
                doc_count = doc_count + 1
                if len(operations) > 99:
                    batch_num = batch_num + 1
                    insert_batch(vcore, operations, batch_num, "person")
                    operations = list()
            except Exception as e:
                logging.info("error processing person {}: {}".format(p, str(e)))
    if len(operations) > 0:
        batch_num = batch_num + 1
        insert_batch(vcore, operations, batch_num, "person")

    names = None  # gargage collect
    time.sleep(1.0)

    # read the TITLES_FILE, load to the 'imdb' container
    titles = load_titles()
    operations = list()
    for idx, tconst in enumerate(sorted(titles.keys())):
        if idx < max_load_idx:
            try:
                m = titles[tconst]
                m["_id"] = str(uuid.uuid4())
                m["doctype"] = "movie"
                operations.append(InsertOne(m))
                doc_count = doc_count + 1
                if len(operations) > 99:
                    batch_num = batch_num + 1
                    insert_batch(vcore, operations, batch_num, "movie")
                    operations = list()
            except Exception as e:
                logging.info("error processing movie {}: {}".format(t, str(e)))
    if len(operations) > 0:
        batch_num = batch_num + 1
        insert_batch(vcore, operations, batch_num, "movie")

    t2 = time.perf_counter()
    seconds = f"{(t2 - t1):.9f}"
    print("vcore loaded in {} seconds, {} documents, {} batches".format(
        seconds, doc_count, batch_num))

def insert_batch(vcore, operations, batch_num, doctype):
    try:
        print("executing batch {} with {} operations, doctype {}".format(
            batch_num, len(operations), doctype))
        result = vcore.get_coll().bulk_write(operations)
        print(result)
    except Exception as e:
        logging.error("error in insert_batch: {}".format(str(e)))
        logging.error(traceback.format_exc())
        
def create_vcore_collections_and_indexes():
    vcore, dbname, cname = connect_to_vcore_graph_source()
    logging.info("using vcore db: {}, collection: {}".format(dbname, cname))

    indexes = vcore.get_coll_indexes(cname)
    logging.info(
        "indexes before:\n{}".format(json.dumps(indexes, sort_keys=False, indent=2))
    )
    vcore.create_simple_index("doctype")
    vcore.create_simple_index("nconst")
    vcore.create_simple_index("tconst")
    indexes = vcore.get_coll_indexes(cname)
    logging.info(
        "{} indexes after:\n{}".format(
            cname, json.dumps(indexes, sort_keys=False, indent=2)
        )
    )

def load_graph_from_vcore():
    g = None
    graph_svc_opts = {}
    graph_svc_opts["display_ontology"] = False
    graph_svc_opts["iterate_graph"] = True
    graph_svc_opts["persist_graph"] = False
    graph_svc = ImdbGraphService(graph_svc_opts)

    if "--queries" in sys.argv:
        rqr: RdfQueryResult = execute_sparql_query(graph_svc, sparql_100_triples_query())
        FS.write_json(rqr.get_data(), "tmp/sparql_100_triples_query.json")
        rqr: RdfQueryResult = execute_sparql_query(graph_svc, sparql_kevin_bacon_movies_query())
        FS.write_json(rqr.get_data(), "tmp/sparql_kevin_bacon_movies_query.json")
        rqr: RdfQueryResult = execute_sparql_query(graph_svc, sparql_footloose_principals_query())
        FS.write_json(rqr.get_data(), "tmp/sparql_footloose_principals_query.json")

def execute_sparql_query(graph_svc: ImdbGraphService, sparql: str) -> RdfQueryResult:
    try:
        print("---")
        print("execute_sparql_query:")
        print(sparql)
        print("")
        rows = list()
        t1 = time.perf_counter()
        rqr : RdfQueryResult = graph_svc.query(sparql)
        t2 = time.perf_counter()
        seconds = f"{(t2 - t1):.9f}"
        print("graph queried in {} seconds, {} triples".format(seconds, len(rows)))
        return rqr
    except Exception as e:
        logging.error("error in execute_sparql_query: {}".format(str(e)))
        logging.error(traceback.format_exc())
        return None

def add_movie_to_graph(g, doc, CNS):
    try:
        tconst = doc["tconst"]
        movieref = URIRef("http://cosmosdb.com/imdb/{}".format(tconst))
        g.add((movieref, RDF.type, CNS.Person))
        g.add((movieref, CNS.title, Literal(doc["title"])))
        g.add((movieref, CNS.year, Literal(doc["year"])))
        g.add((movieref, CNS.rating, Literal(doc["rating"])))

        for genre in doc["genres"]:
            g.add((movieref, CNS.genre, Literal(genre)))

        for nconst in doc["principals"].keys():
            personref = URIRef("http://cosmosdb.com/imdb/{}".format(nconst))
            g.add((movieref, CNS.has_principal, personref))
    except Exception as e:
        logging.error("error in add_person_to_graph:\n{}\n{}".format(doc, str(e)))
        logging.error(traceback.format_exc())

def add_person_to_graph(g, doc, CNS):
    try:
        nconst = doc["nconst"]
        personref = URIRef("http://cosmosdb.com/imdb/{}".format(nconst))
        g.add((personref, RDF.type, CNS.Person))
        g.add((personref, CNS.name, Literal(doc["name"])))
        g.add((personref, CNS.born, Literal(doc["born"])))
        g.add((personref, CNS.died, Literal(doc["died"])))

        for tconst in doc["titles"].keys():
            movieref = URIRef("http://cosmosdb.com/imdb/{}".format(tconst))
            g.add((personref, CNS.in_movie, movieref))
    except Exception as e:
        logging.error("error in add_person_to_graph:\n{}\n{}".format(doc, str(e)))
        logging.error(traceback.format_exc())

# A few IMDb dataset nconst and tconst values:
# fred astaire    = nm0000001
# lauren bacall   = nm0000002
# kevin bacon     = nm0000102
# lori singer     = nm0001742
# kevin costner   = nm0000126
# footloose       = tt0087277
# field of dreams = tt0097351

def sparql_100_triples_query():
    return """
SELECT * WHERE { ?s ?p ?o . } LIMIT 100
""".strip()

def sparql_footloose_principals_query():
    return """
PREFIX c: <http://cosmosdb.com/imdb#> 
SELECT ?o
WHERE {
    <http://cosmosdb.com/imdb/tt0087277> c:has_principal ?o .
}
LIMIT 100
""".strip()

def sparql_kevin_bacon_movies_query():
    return """
PREFIX c: <http://cosmosdb.com/imdb#> 
SELECT ?o
WHERE {
    <http://cosmosdb.com/imdb/nm0000102> c:in_movie ?o .
}
LIMIT 100
""".strip()

def load_titles() -> dict:
    data = FS.read_json(TITLES_FILE)
    print("load_titles, len: {}".format(len(data)))
    return data

def load_names_filtered() -> dict:
    data = FS.read_json(NAMES_FILTERED_FILE)
    print("load_names_filtered, len: {}".format(len(data)))
    return data

def build_az_cli_env_vars():
    """ build the --env-vars line for the 'az containerapp create' command """
    # See the docker-compose.yml file; the same list of env vars is used there
    envvars, pairs = list(), list()
    envvars.append("CAIG_AZURE_OPENAI_COMPLETIONS_DEP")
    envvars.append("CAIG_AZURE_OPENAI_EMBEDDINGS_DEP")
    envvars.append("CAIG_AZURE_OPENAI_KEY")
    envvars.append("CAIG_AZURE_OPENAI_URL")
    envvars.append("CAIG_GRAPH_SOURCE_TYPE")
    envvars.append("CAIG_AZURE_MONGO_VCORE_CONN_STR")
    envvars.append("CAIG_GRAPH_SOURCE_DB")
    envvars.append("CAIG_GRAPH_SOURCE_CONTAINER")
    envvars.append("CAIG_GRAPH_SOURCE_OWL_FILENAME")
    envvars.append("CAIG_GRAPH_SOURCE_RDF_FILENAME")
    envvars.append("CAIG_DEFINED_AUTH_USERS")
    envvars.append("CAIG_LOG_LEVEL")
    envvars.append("PORT")
    envvars.append("WEB_CONCURRENCY")
    for name in envvars:
        try:
            val = os.environ[name]
            if name == "CAIG_AZURE_MONGO_VCORE_CONN_STR":
                pairs.append("'{}=xxx'".format(name))
            elif name == "CAIG_DEFINED_AUTH_USERS":
                pairs.append("'{}=xxx'".format(name))
            else:
                pairs.append("'{}={}'".format(name, val))
        except:
            val = 'xxx'
            pairs.append("'{}={}'".format(name, val))
    joined = " ".join(pairs)
    result = "--env-vars {}".format(joined)
    print(result)


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
            if func == "display_caig_env_vars":
                display_caig_env_vars()
            elif func == "create_vcore_collections_and_indexes":
                create_vcore_collections_and_indexes()
            elif func == "load_vcore":
                load_vcore()
            elif func == "load_graph_from_vcore":
                load_graph_from_vcore()
            elif func == "build_az_cli_env_vars":
                build_az_cli_env_vars()
            else:
                print_options("Error: invalid function: {}".format(func))
        except Exception as e:
            logging.info(str(e))
            logging.info(traceback.format_exc())
