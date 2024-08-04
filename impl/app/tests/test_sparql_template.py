import pytest

from src.util.sparql_template import SparqlTemplate
from src.services.config_service import ConfigService


def test_developers_of_library():
    ConfigService.set_standard_unit_test_env_vars()
    values = dict()
    values["id"] = "pypi_swift"
    values["limit"] = 1989
    text = SparqlTemplate().render("developers_of_library.txt", values)
    expected = """
PREFIX c: <http://cosmosdb.com/caig#>
SELECT ?o
WHERE {
    <http://cosmosdb.com/caig/pypi_swift> c:developed_by ?o .
}
LIMIT 1989
""".strip()
    assert text == expected
