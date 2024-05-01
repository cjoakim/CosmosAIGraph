import os
import json
import logging
import time
import traceback

import rdflib

from rdflib import Graph, Literal, RDF, URIRef, BNode

# rdflib knows about quite a few popular namespaces, like W3C ontologies, schema.org etc.
from rdflib.namespace import CSVW, DC, DCAT, DCTERMS, DOAP, FOAF, ODRL2, ORG, OWL
from rdflib.namespace import PROF, PROV, RDF, RDFS, SDO, SH, SKOS, SOSA, SSN, TIME
from rdflib.namespace import VOID, XSD
from rdflib.namespace import Namespace, NamespaceManager

from rdflib.extras.infixowl import (
    AllClasses,
    AllProperties,
    BooleanClass,
    Class,
    ClassNamespaceFactory,
    CommonNSBindings,
    ComponentTerms,
    DeepClassClear,
    EnumeratedClass,
    GetIdentifiedClasses,
    Individual,
    Infix,
    MalformedClassError,
    Property,
    Restriction,
    classOrTerm,
    exactly,
    generateQName,
    max,
    min,
    only,
    some,
    value,
)

from pysrc.services.config_service import ConfigService
from pysrc.services.imdb_graph_builder import ImdbGraphBuilder
from pysrc.models.internal_models import OwlInfo
from pysrc.models.rdf_query_result import RdfQueryResult
from pysrc.util.fs import FS
from pysrc.util.sparql_formatter import SparqlFormatter
from pysrc.util.sparql_template import SparqlTemplate

# Instances of this class contain the in-memory rdflib graph,
# and are use to interact with and query the graph via the SPARQL query syntax.
# See https://rdflib.readthedocs.io/en/stable/
# Chris Joakim, Microsoft


class ImdbGraphService:
    def __init__(self, opts: dict):
        self.opts = opts
        gb = ImdbGraphBuilder(opts)
        self.graph = gb.build()

    def reload(self):
        gb = ImdbGraphBuilder(self.opts)
        self.graph = gb.build()

    def liveness_check(self) -> dict:
        """
        Return a dict containing the health status of this GraphService.
        The dict resembles a LivenessModel.
        """
        alive = False
        rows_read = 0
        try:
            if self.graph == None:
                rows_read = -1
            else:
                for row in self.graph.query("SELECT * WHERE { ?s ?p ?o . } LIMIT 100"):
                    rows_read = rows_read + 1
                if rows_read > 90:  # 100+ rows are expected, including the OWL content
                    alive = True
        except Exception as e:
            rows_read = -2
            logging.critical((str(e)))
            logging.exception(e, stack_info=True, exc_info=True)
        data = dict()
        data["alive"] = alive
        data["rows_read"] = rows_read
        data["epoch"] = time.time()
        return data

    def owl_info(self) -> OwlInfo:
        """Return a dict containing the owl filename and owl content"""
        resp_obj = dict()
        resp_obj["ontology_file"] = ""
        resp_obj["owl"] = ""
        resp_obj["error"] = None
        try:
            ontology_file = ConfigService.graph_source_owl_filename()
            resp_obj["ontology_file"] = ontology_file
            resp_obj["owl"] = FS.read(ontology_file)
        except Exception as e:
            resp_obj["error"] = str(e)
            logging.critical((str(e)))
            logging.exception(e, stack_info=True, exc_info=True)
        return resp_obj

    def query(self, sparql) -> RdfQueryResult:
        """
        Query the in-memory graph with the given SPARQL.
        Return a RdfQueryResult object.
        """
        rqr = RdfQueryResult(sparql)
        try:
            if sparql == None:
                rqr.set_exception("given sparql is None")
                return rqr
            sparql = SparqlFormatter().pretty(sparql)  # ensure a PREFIX is present

            if self._valid_query(sparql):
                logging.info("GraphService - query: {}".format(sparql))
                for row in self.graph.query(sparql):
                    # row is an instance of <class 'rdflib.query.ResultRow'>
                    rqr.add_row(row)
                rqr.set_results(self._reduce_query_results(rqr.get_rows()))
            else:
                rqr.set_exception("invalid query; not executed")
        except Exception as e:
            rqr.set_exception(str(e))
            logging.critical((str(e)))
            logging.exception(e, stack_info=True, exc_info=True)
        rqr.finish()
        return rqr

    ########## PRIVATE METHODS BELOW ##########

    def _valid_query(self, sparql):
        return True  # TODO - implement

    def _reduce_query_results(self, result_rows):
        """
        Return a list of dictionary objects, one per result row,
        from the given list of <class 'rdflib.query.ResultRow'> objects.
        """
        reduced = list()
        if result_rows is not None:
            for result_row in result_rows:
                d = result_row.asdict()
                keys = list(d.keys())
                for key in keys:
                    d[key] = str(d[key])
                reduced.append(d)
        return reduced

    def _execute_query(self, sparql) -> RdfQueryResult:
        """return a dict with a 'rows' key containing a list, and an optional 'exception' key containing a str"""
        rqr = RdfQueryResult(sparql)
        logging.debug("_execute_query: {}".format(sparql))
        if sparql == None:
            rqr.set_exception("the given sparql is None")
            return rqr
        try:
            for row in self.graph.query(sparql):
                rqr.add_row(
                    row
                )  # row is an instance of <class 'rdflib.query.ResultRow'>
        except Exception as e:
            rqr.set_exception(e)
            logging.critical((str(e)))
            logging.exception(e, stack_info=True, exc_info=True)
        rqr.finish()
        return rqr

    def _uriref_id(self, uriref):
        """
        For a rdflib.term.URIRef value like 'http://cosmosdb.com/caig/pypi_click' return 'pypi_click'.
        """
        return str(uriref).split("/")[-1]
