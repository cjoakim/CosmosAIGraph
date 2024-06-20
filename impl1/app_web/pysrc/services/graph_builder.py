import logging
import os
import time

import rdflib

from rdflib import Graph
from rdflib.namespace import Namespace

from pysrc.services.config_service import ConfigService
from pysrc.services.cosmos_vcore_service import CosmosVCoreService
from pysrc.util.rdflib_triples_builder import RdflibTriplesBuilder
from pysrc.util.counter import Counter
from pysrc.util.fs import FS

# Instances of this class are used to build an instance of class GraphService,
# which contains an in-memory rdflib database.  The source data for building
# the graph consists of an Web Ontology File (OWL) as well as either a RDF
# input file (i.e - *.nt) or a Cosmos DB Mongo vCore database.
#
# Chris Joakim, Microsoft


class GraphBuilder:

    def __init__(self, opts={}):
        self.opts = opts

    def initialize_graph(self) -> rdflib.Graph:
        self.cns = self.graph_namespace()
        self.CNS = Namespace(self.cns)  # CNS ~ Custom Namespace
        logging.info("GraphBuilder#initialize_graph - cns: {}".format(self.cns))
        ontology_file = ConfigService.graph_source_owl_filename()
        logging.info(
            "GraphBuilder#initialize_graph - ontology_file: {}".format(ontology_file)
        )
        self.g = Graph()
        self.g.bind(self.graph_namespace_alias(), self.CNS)
        self.g.parse(ontology_file, format="xml")

    def build(self, opts=None) -> rdflib.Graph:
        # Processing steps:
        # 1. Define the custom namespace, CNS
        # 2. Load the custom ontology file
        # 3. Bind that namespace to simply 'c' for brevity
        # 4. Display the defined classes and properties in the ontology
        # 5. Load the graph using the custom ontology

        self.initialize_graph()
        if opts is not None:
            self.opts = opts

        config = ConfigService()
        logging.info(
            "GraphBuilder#build graph_source: {}".format(config.graph_source())
        )

        if config.graph_source() == "rdf_file":
            self.populate_graph_from_rdf_file(self.g, config)
        elif config.graph_source() == "json_file":
            self.populate_graph_from_json_file(self.g, config, self.CNS)
        elif config.graph_source() == "cosmos_vcore":
            self.populate_graph_from_cosmosdb_vcore(self.g, config, self.CNS)
        else:
            logging.critical(
                "WARNING: GraphBuilder defaulting to cosmos_vcore loading strategy"
            )
            self.populate_graph_from_cosmosdb_vcore(self.g, config, self.CNS)

        if "iterate_graph" in self.opts.keys():
            self.iterate_graph(self.g, "after load")
        if "persist_graph" in self.opts.keys():
            self.persist_graph(self.g)
        return self.g

    def graph_namespace(self) -> str:
        """ " return a URI value like 'http://cosmosdb.com/caig#'"""
        return ConfigService.graph_namespace()

    def graph_namespace_alias(self) -> str:
        """ " return a value like 'caig' (from namespace 'http://cosmosdb.com/caig#')"""
        return ConfigService.graph_namespace_alias()

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
            ns = self.graph_namespace().replace("#", "").strip()
            coll = vcore.get_coll()
            docs_read = 0
            tb = RdflibTriplesBuilder()
            t1 = time.perf_counter()

            # Read the appropriate JSON documents from Cosmos DB, and pass
            # each to your RdflibTriplesBuilder to be added to the graph.
            for libtype in ["pypi"]:
                query_spec = {"libtype": libtype}
                projection = self.library_projection_attrs()
                cursor = coll.find(
                    query_spec, projection=projection, skip=0, limit=999999
                )
                for idx, doc in enumerate(cursor):
                    docs_read = docs_read + 1
                    if docs_read % 1000 == 0:
                        logging.info(
                            "GraphBuilder#populate_graph_from_cosmosdb_vcore - libdocs read: {}".format(
                                docs_read
                            )
                        )
                    tb.append_doc_to_graph(g, doc, CNS, ns)
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

    def populate_graph_from_json_file(
        self, g: rdflib.Graph, config: ConfigService, CNS
    ) -> None:
        try:
            logging.info("GraphBuilder#populate_graph_from_json_file")
            ns = self.graph_namespace().replace("#", "").strip()
            docs_read = 0
            t1 = time.perf_counter()
            label_counter = Counter()

            tb = RdflibTriplesBuilder()
            infile = self.opts["cosmos_documents_file"]
            vertices_list = FS.read_json(infile)
            for doc in vertices_list:
                label = doc["label"]
                label_counter.increment(label)
                docs_read = docs_read + 1
                tb.append_doc_to_graph(g, doc, CNS, ns)

            t2 = time.perf_counter()
            seconds = f"{(t2 - t1):.9f}"
            logging.critical(
                "GraphBuilder#populate_graph_from_json_file - {} docs loaded into graph in {}".format(
                    docs_read, seconds
                )
            )
            FS.write_json(label_counter.get_data(), "tmp/graph_builder_labels.json")

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
