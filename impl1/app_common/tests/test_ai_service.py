import json
import os
import time
import pytest

from pysrc.services.ai_service import AiService
from pysrc.services.config_service import ConfigService
from pysrc.util.fs import FS

# pytest tests/test_ai_service.py


def test_constructor():
    ai_svc = AiService()
    assert ai_svc.endpoint.startswith("https://")
    assert ai_svc.endpoint.endswith(".openai.azure.com/")
    assert ai_svc.version.startswith("2023-")
    assert ai_svc.aoai_client is not None


def test_generate_sparql_from_user_prompt():
    ai_svc = AiService()
    owl = FS.read("ontologies/libraries.owl")
    assert owl != None
    assert len(owl) > 1000
    assert len(owl) < 10000
    obj = dict()
    obj["session_id"] = ""
    obj["completion_id"] = ""
    obj["completion_model"] = ""
    obj["prompt_tokens"] = -1
    obj["completion_tokens"] = -1
    obj["total_tokens"] = -1
    obj["sparql"] = ""
    obj["error"] = ""
    obj["natural_language"] = (
        "What are the dependencies of the 'pypi' type of library named 'flask'?"
    )
    obj["owl"] = owl

    result_obj = ai_svc.generate_sparql_from_user_prompt(obj)
    print(obj)
    FS.write_json(obj, "tmp/generate_sparql_from_user_prompt.json")
    assert obj["prompt_tokens"] > 1300
    assert obj["prompt_tokens"] < 1600
    assert obj["completion_tokens"] > 50
    assert obj["completion_tokens"] < 100
    assert obj["total_tokens"] > 1400
    assert obj["total_tokens"] < 1600
    assert obj["elapsed"] > 0.001
    assert obj["sparql"].startswith(
        "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> PREFIX : <http://cosmosdb.com/caig#> SELECT "
    )

    # result_obj is a SparqlGenerationResult model and looks like this:
    # {
    #   "completion_id": "chatcmpl-8tJ9dO8diu9aiU91OJxrW2mTzdId1",
    #   "completion_model": "gpt-4",
    #   "prompt_tokens": 1427,
    #   "completion_tokens": 79,
    #   "total_tokens": 1506,
    #   "elapsed": 2.840292542008683,
    #   "sparql": "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> PREFIX : <http://cosmosdb.com/caig#> SELECT ?dependency WHERE { ?lib :ln 'flask' . ?lib :lt 'pypi' . ?lib :uses_lib ?dependency . }"
    # }
