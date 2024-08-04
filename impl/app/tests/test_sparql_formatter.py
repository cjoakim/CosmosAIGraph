import json
import os
import time
import pytest

from src.util.sparql_formatter import SparqlFormatter

# pytest tests/test_sparql_formatter.py


def test_pretty():
    pretty = SparqlFormatter().pretty(sample_generated_sparql())
    print("---")
    print(pretty)
    print("---")
    assert pretty == sample_expected_sparql()

def test_pretty_noinput():
    pretty = SparqlFormatter().pretty(None)
    assert pretty == None

def test_inject_prefix_and_limit():
    pretty = SparqlFormatter().pretty(no_prefix_query())
    assert pretty.startswith(SparqlFormatter().default_prefix())
    assert pretty.endswith(' LIMIT 100')

def sample_generated_sparql():
    return """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> PREFIX : <http://cosmosdb.com/caig#> SELECT ?dependency ?subDependency WHERE { ?lib :ln 'flask' . ?lib :lt 'pypi' . ?lib :uses_lib ?dependency . OPTIONAL { ?dependency :uses_lib ?subDependency . } }
""".strip()

def no_prefix_query():
    return """
SELECT ?dependencyName WHERE {
  ?lib caig:ln 'flask' .
  ?lib caig:lt 'pypi' .
  ?lib caig:uses_lib ?dependency .
  ?dependency caig:ln ?dependencyName .
}
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
}} LIMIT 100
""".strip()
