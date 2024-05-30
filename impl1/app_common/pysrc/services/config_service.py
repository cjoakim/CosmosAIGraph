import json
import logging
import os
import sys
import time
import traceback

# Instances of this class are used to define and obtain all configuration
# values in this solution.  These are typically obtained at runtime via
# environment variables.
# Chris Joakim, Microsoft


class ConfigService:
    @classmethod
    def defined_environment_variables(cls) -> dict:
        """
        Return a dict with the defined environment variable names and descriptions
        """
        d = dict()
        d["CAIG_HOME"] = (
            "Root directory of the CosmosAIGraph GitHub repository on your system"
        )
        d["CAIG_AZURE_REGION"] = "The Azure region where the ACA app is deployed to"
        d["CAIG_GRAPH_SOURCE_TYPE"] = (
            "The RDF graph data source type, either 'rdf_file' or 'cosmos_vcore'"
        )
        d["CAIG_GRAPH_SOURCE_OWL_FILENAME"] = "The input RDF OWL ontology file"
        d["CAIG_GRAPH_SOURCE_RDF_FILENAME"] = (
            "The RDF input file, if CAIG_GRAPH_SOURCE_TYPE is 'rdf_file'"
        )
        d["CAIG_GRAPH_SOURCE_DB"] = (
            "The graph vCore database name, if CAIG_GRAPH_SOURCE_TYPE is 'cosmos_vcore'"
        )
        d["CAIG_GRAPH_SOURCE_CONTAINER"] = (
            "The graph vCore container name, if CAIG_GRAPH_SOURCE_TYPE is 'cosmos_vcore'"
        )
        d["CAIG_CACHE_CONTAINER"] = "The vCore container for key/value cache"
        d["CAIG_CONFIG_CONTAINER"] = "The vCore container for configuration JSON values"
        d["CAIG_CONVERSATIONS_CONTAINER"] = (
            "The vCore container where the chat conversations and history are persisted"
        )
        d["CAIG_FEEDBACK_CONTAINER"] = (
            "The vCore container where user feedback is persisted"
        )
        d["CAIG_AZURE_MONGO_VCORE_CONN_STR"] = (
            "The full connection string for the Cosmos DB Mongo vCore account"
        )
        d["CAIG_USE_ALT_SPARQL_CONSOLE"] = (
            "A non empty string displays the alt view; defaults to an empty string"
        )
        d["CAIG_AZURE_OPENAI_URL"] = "The URL of your Azure OpenAI account"
        d["CAIG_AZURE_OPENAI_KEY"] = "The Key of your Azure OpenAI account"
        d["CAIG_AZURE_OPENAI_COMPLETIONS_DEP"] = (
            "The name of your Azure OpenAI completions deployment"
        )
        d["CAIG_AZURE_OPENAI_EMBEDDINGS_DEP"] = (
            "The name of your Azure OpenAI embeddings deployment"
        )
        d["CAIG_ACA_ENVIRONMENT_NAME"] = (
            "The Azure Container App (ACA) environment name"
        )
        d["CAIG_LA_WORKSPACE_NAME"] = (
            "The Log Analytics workspace name used by the Azure Container App (ACA)"
        )
        d["CAIG_DEFINED_AUTH_USERS"] = ""
        d["CAIG_WEB_APP_NAME"] = ""
        d["CAIG_WEB_APP_URL"] = ""
        d["CAIG_WEB_APP_PORT"] = ""
        d["CAIG_GRAPH_SERVICE_NAME"] = ""
        d["CAIG_GRAPH_SERVICE_URL"] = ""
        d["CAIG_GRAPH_SERVICE_PORT"] = ""
        d["CAIG_LOG_LEVEL"] = (
            "a python logging standard-lib level name: notset, debug, info, warning, error, or critical"
        )
        return d

    @classmethod
    def sample_environment_variable_values(cls) -> dict:
        d = dict()
        d["CAIG_HOME"] = ""
        d["CAIG_AZURE_REGION"] = "eastus"
        d["CAIG_GRAPH_SOURCE_TYPE"] = "cosmos_vcore"
        d["CAIG_GRAPH_SOURCE_OWL_FILENAME"] = "ontologies/libraries.owl"
        d["CAIG_GRAPH_SOURCE_RDF_FILENAME"] = "rdf/libraries-graph.nt"
        d["CAIG_GRAPH_SOURCE_DB"] = "caig"
        d["CAIG_GRAPH_SOURCE_CONTAINER"] = "libraries"
        d["CAIG_CACHE_CONTAINER"] = "cache"
        d["CAIG_CONFIG_CONTAINER"] = "config"
        d["CAIG_CONVERSATIONS_CONTAINER"] = "conversations"
        d["CAIG_AZURE_MONGO_VCORE_CONN_STR"] = "mongodb+srv://..."
        d["CAIG_USE_ALT_SPARQL_CONSOLE"] = ""
        d["CAIG_AZURE_OPENAI_URL"] = ""
        d["CAIG_AZURE_OPENAI_KEY"] = ""
        d["CAIG_AZURE_OPENAI_COMPLETIONS_DEP"] = "gpt4"
        d["CAIG_AZURE_OPENAI_EMBEDDINGS_DEP"] = "embeddings"
        d["CAIG_DEFINED_AUTH_USERS"] = "guest:secret"
        d["CAIG_ACA_ENVIRONMENT_NAME"] = "caig"
        d["CAIG_LA_WORKSPACE_NAME"] = "caig"
        d["CAIG_WEB_APP_NAME"] = "caig-web"
        d["CAIG_WEB_APP_URL"] = "http://127.0.0.1"
        d["CAIG_WEB_APP_PORT"] = "8000"
        d["CAIG_GRAPH_SERVICE_NAME"] = "caig-graph"
        d["CAIG_GRAPH_SERVICE_URL"] = "http://graph_service"
        d["CAIG_GRAPH_SERVICE_PORT"] = "8001"
        d["CAIG_LOG_LEVEL"] = "info"
        return d

    @classmethod
    def log_defined_env_vars(cls):
        """Log the defined CAIG_ environment variables as JSON"""
        keys = sorted(cls.defined_environment_variables().keys())
        selected = dict()
        for key in keys:
            value = cls.envvar(key)
            selected[key] = value
        logging.info(
            "log_config: {}".format(json.dumps(selected, sort_keys=True, indent=2))
        )

    @classmethod
    def graph_service_port(cls) -> str:
        return cls.envvar("CAIG_GRAPH_SERVICE_PORT", "8001")

    @classmethod
    def graph_service_url(cls) -> str:
        return cls.envvar("CAIG_GRAPH_SERVICE_URL", "http://127.0.0.1")

    @classmethod
    def graph_source(cls) -> str:
        return cls.envvar("CAIG_GRAPH_SOURCE_TYPE", "cosmos_vcore")

    @classmethod
    def graph_source_owl_filename(cls) -> str:
        return cls.envvar("CAIG_GRAPH_SOURCE_OWL_FILENAME", "ontologies/libraries.owl")

    @classmethod
    def graph_source_rdf_filename(cls) -> str:
        return cls.envvar("CAIG_GRAPH_SOURCE_RDF_FILENAME", "rdf/libraries-graph.nt")

    @classmethod
    def graph_source_db(cls) -> str:
        return cls.envvar("CAIG_GRAPH_SOURCE_DB", "caig")

    @classmethod
    def graph_source_container(cls) -> str:
        return cls.envvar("CAIG_GRAPH_SOURCE_CONTAINER", "libraries")

    @classmethod
    def cache_container(cls) -> str:
        return cls.envvar("CAIG_CACHE_CONTAINER", "cache")

    @classmethod
    def config_container(cls) -> str:
        return cls.envvar("CAIG_CONFIG_CONTAINER", "config")

    @classmethod
    def conversations_container(cls) -> str:
        return cls.envvar("CAIG_CONVERSATIONS_CONTAINER", "conversations")

    @classmethod
    def feedback_container(cls) -> str:
        return cls.envvar("CAIG_FEEDBACK_CONTAINER", "feedback")

    @classmethod
    def mongo_vcore_conn_str(cls) -> str:
        return cls.envvar("CAIG_AZURE_MONGO_VCORE_CONN_STR", None)

    @classmethod
    def use_alt_sparql_console(cls) -> str:
        return len(cls.envvar("CAIG_USE_ALT_SPARQL_CONSOLE", "")) > 0

    @classmethod
    def azure_openai_url(cls) -> str:
        return cls.envvar("CAIG_AZURE_OPENAI_URL", None)

    @classmethod
    def azure_openai_key(cls) -> str:
        return cls.envvar("CAIG_AZURE_OPENAI_KEY", None)

    @classmethod
    def azure_openai_version(cls) -> str:
        return cls.envvar("CAIG_AZURE_OPENAI_VERSION", "2023-12-01-preview")

    @classmethod
    def azure_openai_completions_deployment(cls) -> str:
        return cls.envvar("CAIG_AZURE_OPENAI_COMPLETIONS_DEP", "gpt4")

    @classmethod
    def azure_openai_embeddings_deployment(cls) -> str:
        return cls.envvar("CAIG_AZURE_OPENAI_EMBEDDINGS_DEP", "embeddings")

    @classmethod
    def libraries_namespace(cls):
        return "http://cosmosdb.com/caig#"

    @classmethod
    def defined_auth_users(cls) -> dict:
        """
        This is a primitive authentication and authorization mechanism for demonstration purposes only.
        Customers should implement authentication and authorization, such as with the 'pyad' library -
        see https://pypi.org/project/pyad/
        """
        users = dict()
        try:
            s = cls.envvar(
                "CAIG_DEFINED_AUTH_USERS", "guest:secret|chris:clt|aleksey:mia"
            )
            for pair in s.split("|"):
                tokens = pair.split(":")
                if len(tokens) == 2:
                    usr, pwd = tokens[0], tokens[1]
                    users[usr] = pwd
        except Exception as e:
            logging.critical(str(e))
            logging.exception(e, stack_info=True, exc_info=True)
            return None
        return users

    @classmethod
    def envvar(cls, name: str, default: str = "") -> str:
        """Return the value of the given environment variable name, or the given default value."""
        if name in os.environ:
            return os.environ[name]
        return default

    @classmethod
    def epoch(cls) -> float:
        """Return the current epoch time, as time.time()"""
        return time.time()

    @classmethod
    def verbose(cls) -> bool:
        """Return a boolean indicating if --verbose or -v is in the command-line."""
        flags = ["--verbose", "-v"]
        for arg in sys.argv:
            for flag in flags:
                if arg == flag:
                    return True
        return False

    @classmethod
    def boolean_arg(cls, flag: str) -> bool:
        """Return a boolean indicating if the given arg is in the command-line."""
        for arg in sys.argv:
            if arg == flag:
                return True
        return False

    @classmethod
    def set_standard_unit_test_env_vars(cls):
        """Set environment variables for most unit tests"""
        os.environ["CAIG_GRAPH_SOURCE_TYPE"] = "rdf_file"
        os.environ["CAIG_GRAPH_SOURCE_OWL_FILENAME"] = "ontologies/libraries.owl"
        os.environ["CAIG_GRAPH_SOURCE_RDF_FILENAME"] = "rdf/libraries-graph-mini.nt"
