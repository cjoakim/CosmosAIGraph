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
from pysrc.services.cosmos_vcore_service import CosmosVCoreService
from pysrc.util.fs import FS

# Instances of this class are used to build an instance of class GraphService,
# which contains an in-memory rdflib database.  The source data for building
# the graph consists of an Web Ontology File (OWL) as well as either a RDF
# input file (i.e - *.nt) or a Cosmos DB Mongo vCore database.
#
# The source is specified at runtime via with several environment variables, including:
# - CAIG_GRAPH_SOURCE_TYPE
# - CAIG_GRAPH_SOURCE_OWL_FILENAME
# - CAIG_GRAPH_SOURCE_RDF_FILENAME
# - CAIG_GRAPH_SOURCE_DB
# - CAIG_GRAPH_SOURCE_CONTAINER
# - CAIG_AZURE_MONGO_VCORE_CONN_STR
#
# See class ConfigService for a description of these environment variables.
# See the docker-compose.yml file
# Chris Joakim, Microsoft


class GraphBuilder:
    def __init__(self):
        pass

    def build(self, opts={}) -> rdflib.Graph:
        # Processing steps:
        # 1. Define the custom namespace, CNS
        # 2. Load the custom ontology file
        # 3. Bind that namespace to simply 'c' for brevity
        # 4. Display the defined classes and properties in the ontology
        # 5. Load the graph using the custom ontology

        CNS = Namespace(self.libraries_namespace())  # CNS ~ Custom Namespace
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

        if "display_ontology" in opts.keys():
            self.display_ontology_classes_and_properties(g)
        if "iterate_graph" in opts.keys():
            self.iterate_graph(g, "after load")
        if "persist_graph" in opts.keys():
            self.persist_graph(g)
        return g

    def libraries_namespace(self) -> str:
        return "http://cosmosdb.com/caig#"

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
            logging.info("GraphBuilder#populate_graph_from_cosmosdb_vcore")
            vcore, dbname, cname = self.connect_to_vcore_graph_source()
            coll = vcore.get_coll()
            docs_read = 0
            t1 = time.perf_counter()
            for libtype in ["pypi"]:
                query_spec = {"libtype": libtype}
                projection = self.library_projection_attrs()
                cursor = coll.find(
                    query_spec, projection=projection, skip=0, limit=999999
                )
                for idx, libdoc in enumerate(cursor):
                    docs_read = docs_read + 1
                    if docs_read % 1000 == 0:
                        logging.info(
                            "GraphBuilder#populate_graph_from_cosmosdb_vcore - libdocs read: {}".format(
                                docs_read
                            )
                        )
                    self.append_lib_to_graph(g, libdoc, CNS)
            t2 = time.perf_counter()
            seconds = f"{(t2 - t1):.9f}"
            logging.critical(
                "GraphBuilder#populate_graph_from_cosmosdb_vcore - {} docs loaded into graph in {}".format(
                    docs_read, seconds
                )
            )
        except Exception as e:
            logging.critical(str(e))
            logging.exception(e, stack_info=True, exc_info=True)
            return None

    def library_projection_attrs(self):
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

    def connect_to_vcore_graph_source(self):
        """
        connect to the vcore account, and return a 3-tuple of
        (vcore, dbname, cname), where vcore is an instance of
        class CosmosVCoreService.
        """
        opts = dict()
        opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
        vcore = CosmosVCoreService(opts)
        if "pymongo.mongo_client.MongoClient" in str(type(vcore.get_client())):
            logging.critical(
                "GraphBuilder#connect_to_vcore_graph_source - connected to vcore"
            )
        else:
            logging.critical(
                "GraphBuilder#connect_to_vcore_graph_source - unable to connect to vcore"
            )
            return
        dbname = ConfigService.graph_source_db()
        cname = ConfigService.graph_source_container()
        vcore.set_db(dbname)
        vcore.set_coll(cname)
        return (vcore, dbname, cname)

    def append_lib_to_graph(self, g, libdoc, CNS):
        """
        The graph is build from these attributes in each libdoc:
        name, libtype, license_kwds, kwds, developers, dependency_ids
        """
        id = libdoc["id"]
        eref = URIRef("http://cosmosdb.com/caig/{}".format(id))
        g.add((eref, RDF.type, CNS.Lib))
        g.add((eref, CNS.ln, Literal(libdoc["name"])))
        g.add((eref, CNS.lt, Literal(libdoc["libtype"])))
        g.add((eref, CNS.lic, Literal(libdoc["license_kwds"])))
        g.add((eref, CNS.kwds, Literal(libdoc["kwds"])))

        for dev in libdoc["developers"]:
            devref = URIRef("http://cosmosdb.com/caig/{}".format(dev))
            libref = URIRef("http://cosmosdb.com/caig/{}".format(id))
            g.add((eref, RDF.type, CNS.Dev))
            g.add((devref, CNS.developer_of, libref))
            g.add((libref, CNS.developed_by, devref))

        for dep_lib in libdoc["dependency_ids"]:
            pass
            libref = URIRef("http://cosmosdb.com/caig/{}".format(id))
            depref = URIRef("http://cosmosdb.com/caig/{}".format(dep_lib))
            g.add((libref, CNS.uses_lib, depref))
            g.add((depref, CNS.used_by_lib, libref))

    def persist_graph(self, g, outfile="tmp/graph.nt"):
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
