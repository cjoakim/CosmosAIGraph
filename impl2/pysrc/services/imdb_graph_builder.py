import logging
import os
import psutil
import time
import traceback

import rdflib

from rdflib import Graph, Literal, RDF, URIRef, BNode
from rdflib.namespace import Namespace, NamespaceManager

from rdflib.extras.infixowl import AllClasses, AllProperties, GetIdentifiedClasses

from pysrc.services.config_service import ConfigService
from pysrc.services.cosmos_vcore import CosmosVCore
from pysrc.util.fs import FS

# Instances of this class are used to build an instance of class GraphService,
# which contains an in-memory rdflib database.  The source data for building
# the graph consists of an Web Ontology File (OWL) as well as either a RDF
# input file (i.e - *.nt) or a Cosmos DB Mongo vCore database.
#
# Chris Joakim, Microsoft


class ImdbGraphBuilder:
    def __init__(self, opts):
        self.opts = opts

    def build(self) -> rdflib.Graph:
        # Processing steps:
        # 1. Define the custom namespace, CNS
        # 2. Load the custom ontology file
        # 3. Bind that namespace to simply 'c' for brevity
        # 4. Display the defined classes and properties in the ontology
        # 5. Load the graph using the custom ontology

        CNS = Namespace(self.custom_namespace())  # CNS ~ Custom Namespace
        cwd = psutil.Process().cwd()
        logging.info("GraphBuilder#build - cwd: {}".format(cwd))
        ontology_file = ConfigService.graph_source_owl_filename()
        logging.info("GraphBuilder#build - ontology_file: {}".format(ontology_file))
        g = Graph()
        g.bind("c", CNS)
        g.parse(ontology_file, format="xml")

        # The in-memory graph can be loaded from either a static rdf nt file,
        # or a dynamic set of Cosmos DB Mongo vCore documents.  Loading from
        # rdf nt files is only recommended for initial development and unit testing.
        config = ConfigService()
        if config.graph_source() == "rdf_file":
            self.populate_graph_from_rdf_file(g, config)
        elif config.graph_source() == "cosmos_vcore":
            self.populate_graph_from_cosmosdb_vcore(g, config, CNS)
        else:
            logging.critical(
                "WARNING: GraphBuilder defaulting to cosmos_vcore loading strategy"
            )
            self.populate_graph_from_cosmosdb_vcore(g, config, CNS)

        if "display_ontology" in self.opts.keys():
            if self.opts["display_ontology"] == True:
                self.display_ontology_classes_and_properties(g)
        if "iterate_graph" in self.opts.keys():
            if self.opts["iterate_graph"] == True:
                self.iterate_graph(g, "after load")
        if "persist_graph" in self.opts.keys():
            if self.opts["persist_graph"] == True:
                self.persist_graph(g)
        return g

    def custom_namespace(self) -> str:
        return "http://cosmosdb.com/imdb#"

    def display_ontology_classes_and_properties(self, g) -> None:
        logging.info("=== GraphBuilder Ontology GetIdentifiedClasses ===")
        classes = list(GetIdentifiedClasses(g))
        for idx, c in enumerate(classes):
            logging.info("{} {}".format(idx, c))

        logging.info("=== GraphBuilder Ontology AllClasses ===")
        classes = list(AllClasses(g))
        for idx, c in enumerate(classes):
            logging.info("{} {}".format(idx, c))

        logging.info("=== GraphBuilder Ontology AllProperties ===")
        properties = list(AllProperties(g))
        for idx, p in enumerate(properties):
            logging.info("{} {}".format(idx, p))

    def populate_graph_from_rdf_file(
        self, g: rdflib.Graph, config: ConfigService
    ) -> None:
        """Load the graph from a RDF (nt) triples file"""
        try:
            cwd = os.getcwd()
            rdf_file = config.graph_source_rdf_filename()
            fq_filename = "{}{}{}".format(cwd, os.sep, rdf_file)
            file_format = "nt"
            logging.info(
                "GraphBuilder#populate_graph_from_rdf_file: {}, format: {}".format(
                    fq_filename, file_format
                )
            )
            t1 = time.perf_counter()
            g.parse(fq_filename, format=file_format)
            t2 = time.perf_counter()
            seconds = f"{(t2 - t1):.9f}"
            logging.critical(
                "GraphBuilder#populate_graph_from_rdf_file - graph loaded in {}".format(
                    seconds
                )
            )
        except Exception as e:
            logging.critical(str(e))
            logging.exception(e, stack_info=True, exc_info=True)
            return None

    def populate_graph_from_cosmosdb_vcore(
        self, g: rdflib.Graph, config: ConfigService, CNS
    ) -> None:
        try:
            vcore, dbname, cname = self.connect_to_vcore_graph_source()
            coll = vcore.get_coll()
            cursor_limit = 9999999
            logging_interval = 10000
            documents_read = 0
            t1 = time.perf_counter()

            query_spec = {"doctype": "movie"}
            cursor = coll.find(query_spec, skip=0, limit=cursor_limit)
            for idx, doc in enumerate(cursor):
                documents_read = documents_read + 1
                if (idx % logging_interval) == 0:
                    print("adding movie doc: {} {}".format(idx, doc))
                self.add_movie_to_graph(g, doc, CNS)

            query_spec = {"doctype": "person"}
            cursor = coll.find(query_spec, skip=0, limit=cursor_limit)
            for idx, doc in enumerate(cursor):
                documents_read = documents_read + 1
                if (idx % logging_interval) == 0:
                    print("adding person doc: {} {}".format(idx, doc))
                self.add_person_to_graph(g, doc, CNS)

            t2 = time.perf_counter()
            seconds = f"{(t2 - t1):.9f}"
            print("load_graph_from_vcore - graph loaded in {} seconds, {} documents".format(
                seconds, documents_read))

            triples = 0
            t1 = time.perf_counter()
            for s, p, o in g:  # Iterate the graph, counting the triples
                triples = triples + 1
            t2 = time.perf_counter()
            seconds = f"{(t2 - t1):.9f}"
            print("load_graph_from_vcore - graph iterated in {} seconds, {} triples".format(
                seconds, triples))
        except Exception as e:
            logging.error("error in populate_graph_from_cosmosdb_vcore: {}".format(str(e)))
            logging.error(traceback.format_exc())

    def connect_to_vcore_graph_source(self):
        """
        connect to the vcore account, and return a 3-tuple of
        (vcore, dbname, cname), where vcore is an instance of
        class CosmosVCoreService.
        """
        opts = dict()
        opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
        vcore = CosmosVCore(opts)
        if "pymongo.mongo_client.MongoClient" in str(type(vcore.get_client())):
            logging.critical(
                "ImdbGraphBuilder#connect_to_vcore_graph_source - connected to vcore"
            )
        else:
            logging.critical(
                "ImdbGraphBuilder#connect_to_vcore_graph_source - unable to connect to vcore"
            )
            return
        dbname = ConfigService.graph_source_db()
        cname = ConfigService.graph_source_container()  # imdb
        vcore.set_db(dbname)
        vcore.set_coll(cname)
        return (vcore, dbname, cname)

    def add_movie_to_graph(self, g, doc, CNS):
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

    def add_person_to_graph(self, g, doc, CNS):
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

    def persist_graph(self, g, outfile="tmp/imdb.nt"):
        logging.info("GraphBuilder#persist_graph start")
        t1 = time.perf_counter()
        g.serialize(format="nt", destination=outfile, encoding="utf-8")
        t2 = time.perf_counter()
        seconds = f"{(t2 - t1):.9f}"
        logging.critical(
            "GraphBuilder#persist_graph - graph written to file {} in {}".format(
                outfile, seconds
            )
        )

    def iterate_graph(self, g, comment):
        logging.info("GraphBuilder#iterate_graph start {} ...".format(comment))
        count = 0
        t1 = time.perf_counter()
        for s, p, o in g:  # Iterate the graph, counting the triples
            count = count + 1
        t2 = time.perf_counter()
        seconds = f"{(t2 - t1):.9f}"
        logging.critical(
            "GraphBuilder#iterate_graph completed, count: {} seconds: {}".format(
                count, seconds
            )
        )
