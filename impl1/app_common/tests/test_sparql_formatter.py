import json
import os
import time
import pytest

from pysrc.util.sparql_formatter import SparqlFormatter

# pytest tests/test_sparql_formatter.py


def test_pretty():
    sf = SparqlFormatter()
    pretty = sf.pretty(sample_generated_sparql())
    print("---")
    print(pretty)
    print("---")
    assert pretty == sample_expected_sparql()


def sample_generated_sparql():
    return """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> PREFIX : <http://cosmosdb.com/caig#> SELECT ?dependency ?subDependency WHERE { ?lib :ln 'flask' . ?lib :lt 'pypi' . ?lib :uses_lib ?dependency . OPTIONAL { ?dependency :uses_lib ?subDependency . } }
""".strip()


def sample_expected_sparql():
    return """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
PREFIX : <http://cosmosdb.com/caig#> 
SELECT ?dependency ?subDependency 
WHERE { 
    ?lib :ln 'flask' . 
    ?lib :lt 'pypi' . 
    ?lib :uses_lib ?dependency . 
    OPTIONAL { ?dependency :uses_lib ?subDependency . 
}}
""".strip()
