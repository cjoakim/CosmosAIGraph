import os
import pytest

from pysrc.services.config_service import ConfigService

# pytest tests/test_config_service.py


def test_graph_namespace():
    ConfigService.set_standard_unit_test_env_vars()
    assert ConfigService.graph_namespace() == "http://cosmosdb.com/caig#"

def test_graph_namespace_alias():
    ConfigService.set_standard_unit_test_env_vars()
    assert ConfigService.graph_namespace_alias() == "caig"

def test_graph_source():
    ConfigService.set_standard_unit_test_env_vars()
    assert ConfigService.graph_source() == "rdf_file"


def test_graph_source_owl_filename():
    ConfigService.set_standard_unit_test_env_vars()
    assert ConfigService.graph_source_owl_filename() == "ontologies/libraries.owl"


def test_graph_source_rdf_filename():
    ConfigService.set_standard_unit_test_env_vars()
    assert ConfigService.graph_source_rdf_filename() == "rdf/libraries-graph-mini.nt"


def test_graph_source_db():
    ConfigService.set_standard_unit_test_env_vars()
    assert ConfigService.graph_source_db() == "caig"


def test_graph_source_container():
    ConfigService.set_standard_unit_test_env_vars()
    assert ConfigService.graph_source_container() == "libraries"


def test_mongo_vcore_conn_str():
    ConfigService.set_standard_unit_test_env_vars()
    val = ConfigService.mongo_vcore_conn_str()
    assert val != None
    assert val.startswith("mongodb+srv://")
    assert ".mongocluster.cosmos.azure.com" in val


def test_azure_openai_url():
    ConfigService.set_standard_unit_test_env_vars()
    val = ConfigService.azure_openai_url()
    assert val != None
    assert val.startswith("https://")
    assert ".openai.azure.com/" in val


def test_azure_openai_key():
    ConfigService.set_standard_unit_test_env_vars()
    val = ConfigService.azure_openai_key()
    assert val != None
    assert len(val) > 30
    assert len(val) < 50


def test_azure_openai_version():
    ConfigService.set_standard_unit_test_env_vars()
    val = ConfigService.azure_openai_version()
    assert val.startswith("2023")


def test_azure_openai_deployment_names():
    ConfigService.set_standard_unit_test_env_vars()
    completions = ConfigService.azure_openai_completions_deployment()
    embeddings = ConfigService.azure_openai_embeddings_deployment()
    assert completions == "gpt4"
    assert embeddings == "embeddings"


def test_use_alt_sparql_console():
    ConfigService.set_standard_unit_test_env_vars()
    envvar = ConfigService.envvar("CAIG_USE_ALT_SPARQL_CONSOLE")
    bool = ConfigService.use_alt_sparql_console()
    if len(envvar) == 0:
        assert bool == False
    else:
        assert bool == True
