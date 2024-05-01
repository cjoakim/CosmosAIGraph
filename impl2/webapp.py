# This is the entry-point for this web application, built with the
# FastAPI web framework
#
# Chris Joakim

import json
import logging
import time

import httpx

from dotenv import load_dotenv

from fastapi import FastAPI, Request, Response, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Pydantic models defining the "shapes" of requests and responses
from pysrc.models.webservice_models import PingModel
from pysrc.models.webservice_models import LivenessModel
from pysrc.models.webservice_models import OwlInfoModel

from pysrc.models.webservice_models import SparqlGenerationRequestModel
from pysrc.models.webservice_models import SparqlGenerationResponseModel


from pysrc.models.rdf_query_result import RdfQueryResult
from pysrc.services.ai_service import AiService
from pysrc.services.config_service import ConfigService
from pysrc.services.cosmos_vcore import CosmosVCore
from pysrc.services.imdb_graph_service import ImdbGraphService
from pysrc.services.logging_level_service import LoggingLevelService
from pysrc.util.fs import FS
from pysrc.util.sparql_formatter import SparqlFormatter
from pysrc.services.ontology_service import OntologyService

# App Startup Logic - create the several services, such as env vars and config,
# AiService, OntologyService, ImdbGraphService, and CosmosVCore then the FastAPI
# app object itself.

load_dotenv(override=True)
logging.basicConfig(
    format="%(asctime)s - %(message)s", level=LoggingLevelService.get_level()
)
ConfigService.log_defined_env_vars()
ai_svc = AiService()
ontology_svc = OntologyService()
owl_xml = ontology_svc.get_owl_content()
logging.info("owl_xml:\n{}".format(owl_xml))

graph_svc_opts = {}
graph_svc_opts["display_ontology"] = False
graph_svc_opts["iterate_graph"] = True
graph_svc_opts["persist_graph"] = False
graph_svc = ImdbGraphService(graph_svc_opts)

vcore_opts = dict()
vcore_opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
logging.info("vcore_opts: {}".format(vcore_opts))
vcore = CosmosVCore(vcore_opts)
vcore.set_db(ConfigService.graph_source_db())

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
views = Jinja2Templates(directory="views")


@app.get("/ping")
async def get_ping() -> PingModel:
    resp = dict()
    resp["epoch"] = str(time.time())
    return resp


@app.get("/liveness")
async def get_liveness(req: Request, resp: Response) -> LivenessModel:
    """
    Return a LivenessModel indicating the health of this web app.
    This endpoint is invoked by the Azure Container Apps (ACA) service.
    The implementation validates the environment variable and url configuration.
    """
    alive = True

    # TODO - implement - check the graph and vcore

    if alive == True:
        resp.status_code = status.HTTP_200_OK
    else:
        resp.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    liveness_data = dict()
    liveness_data["alive"] = alive
    liveness_data["rows_read"] = 0
    liveness_data["epoch"] = time.time()
    logging.info("liveness_check: {}".format(liveness_data))
    return liveness_data


@app.get("/")
async def get_home(req: Request):
    view_data = dict()
    return views.TemplateResponse(request=req, name="home.html", context=view_data)

@app.get("/sparql_console")
async def get_sparql_console(req: Request):
    view_data = get_sparql_console_view_data(req)
    return views.TemplateResponse(
        request=req, name="sparql_console.html", context=view_data
    )

@app.post("/sparql_console")
async def post_sparql_console(req: Request):
    global graph_svc

    form_data = await req.form()  # <class 'starlette.datastructures.FormData'>
    logging.warn("/sparql_console form_data: {}".format(form_data))
    sparql = form_data.get("sparql")
    logging.info("sparql: {}".format(sparql))

    rqr : RdfQueryResult = graph_svc.query(sparql)

    view_data = get_sparql_console_view_data(req)
    view_data["method"] = "post"
    view_data["sparql"] = sparql
    view_data["results_message"] = "Results"
    view_data["results"] = json.dumps(rqr.get_data(), sort_keys=False, indent=2)

    return views.TemplateResponse(
        request=req, name="sparql_console.html", context=view_data
    )

@app.get("/gen_sparql_console")
async def get_ai_console(req: Request):
    view_data = gen_sparql_console_view_data()
    view_data["natural_language"] = (
        "what movies was the actor Kevin Bacon in?"
    )
    view_data["sparql"] = "SELECT * WHERE { ?s ?p ?o . } LIMIT 10"
    return views.TemplateResponse(
        request=req, name="gen_sparql_console.html", context=view_data
    )


@app.post("/gen_sparql_console_generate_sparql")
async def ai_post_gen_sparql(req: Request):
    global owl_xml
    global ai_svc
    global graph_svc

    form_data = await req.form()
    logging.warn("/gen_sparql_console_generate_sparql form_data: {}".format(form_data))
    natural_language = form_data.get("natural_language")
    view_data = gen_sparql_console_view_data()
    view_data["natural_language"] = natural_language
    sparql: str = ""

    resp_obj = dict()
    resp_obj["session_id"] = ""  # TODO
    resp_obj["natural_language"] = natural_language
    resp_obj["owl"] = owl_xml
    resp_obj["completion_id"] = ""
    resp_obj["completion_model"] = ""
    resp_obj["prompt_tokens"] = -1
    resp_obj["completion_tokens"] = -1
    resp_obj["total_tokens"] = -1
    resp_obj["sparql"] = ""
    resp_obj["error"] = ""

    try:
        resp_obj = ai_svc.generate_sparql_from_user_prompt(resp_obj)
        sparql = resp_obj["sparql"]
        view_data["sparql"] = SparqlFormatter().pretty(sparql)
    except Exception as e:
        resp_obj["error"] = str(e)
        logging.critical((str(e)))
        logging.exception(e, stack_info=True, exc_info=True)

    view_data["results"] = json.dumps(resp_obj, sort_keys=False, indent=2)
    view_data["results_message"] = "Generative AI Response"
    return views.TemplateResponse(
        request=req, name="gen_sparql_console.html", context=view_data
    )


@app.post("/gen_sparql_console_execute_sparql")
async def gen_sparql_console_execute_sparql(req: Request):
    global graph_svc

    form_data = await req.form()
    logging.warn("/gen_sparql_console_execute_sparql form_data: {}".format(form_data))
    view_data = gen_sparql_console_view_data()
    sparql = form_data.get("sparql")
    view_data["sparql"] = sparql

    rqr : RdfQueryResult = graph_svc.query(sparql)

    view_data["results"] = json.dumps(rqr.get_data(), sort_keys=False, indent=2)
    view_data["results_message"] = "SPARQL Query Results"
    return views.TemplateResponse(
        request=req, name="gen_sparql_console.html", context=view_data
    )

# non-endpoint methods:

def gen_sparql_console_view_data():
    global owl_xml

    view_data = dict()
    view_data["natural_language"] = (
        "What are the dependencies of the 'pypi' type of library named 'flask'?"
    )
    view_data["sparql"] = ""
    view_data["owl"] = owl_xml
    view_data["results_message"] = ""
    view_data["results"] = ""
    return view_data

# At this time the web application can support up to two different
# SPARQL console views, the libraries view and an alternative view.
# But the UI will show only one of these.
# The logic to handle these two cases is below.

def get_sparql_console_view_data(req: Request) -> dict:
    """Return the view data for the libraries SPARQL console"""

    sample_queries = list()
    sample_queries.append("Count the Triples:\n\n")
    sample_queries.append(sparql_count_query())
    sample_queries.append("\n\n\n")
    sample_queries.append("100 Triples:\n\n")
    sample_queries.append(sparql_100_triples_query())
    sample_queries.append("\n\n\n")
    sample_queries.append("Footloose Principals:\n\n")
    sample_queries.append(sparql_footloose_principals_query())
    sample_queries.append("\n\n\n")
    sample_queries.append("Kevin Bacon Movies:\n\n")
    sample_queries.append(sparql_kevin_bacon_movies_query())
    sample_queries.append("\n\n\n")

    view_data = dict()
    view_data["method"] = "get"
    view_data["sparql"] = sparql_footloose_principals_query()
    view_data["results_message"] = ""
    view_data["results"] = ""
    view_data["sample_sparql_queries"] = "".join(sample_queries)
    return view_data

def sparql_count_query():
    return """
SELECT (COUNT(*) as ?Triples) WHERE { ?s ?p ?o}
""".strip()

def sparql_100_triples_query():
    return """
SELECT * WHERE { ?s ?p ?o . } LIMIT 100
""".strip()

def sparql_footloose_principals_query():
    return """
PREFIX c: <http://cosmosdb.com/imdb#> 
SELECT ?o
WHERE {
    <http://cosmosdb.com/imdb/tt0087277> c:has_principal ?o .
}
LIMIT 100
""".strip()

def sparql_kevin_bacon_movies_query():
    return """
PREFIX c: <http://cosmosdb.com/imdb#> 
SELECT ?o
WHERE {
    <http://cosmosdb.com/imdb/nm0000102> c:in_movie ?o .
}
LIMIT 100
""".strip()
