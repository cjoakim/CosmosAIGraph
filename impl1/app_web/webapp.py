# This is the entry-point for this web application, built with the
# FastAPI web framework
#
# Chris Joakim, Microsoft

import json
import logging
import os
import time
import traceback
import uuid

import httpx

from dotenv import load_dotenv

from fastapi import FastAPI, Request, Response, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Pydantic models defining the "shapes" of requests and responses
from pysrc.models.webservice_models import PingModel
from pysrc.models.webservice_models import LivenessModel
from pysrc.models.webservice_models import OwlInfoModel

# Services with Business Logic
from pysrc.services.cache_service import CacheService
from pysrc.services.config_service import ConfigService
from pysrc.services.logging_level_service import LoggingLevelService
from pysrc.util.fs import FS
from pysrc.util.sparql_formatter import SparqlFormatter

# standard initialization
load_dotenv(override=True)
logging.basicConfig(
    format="%(asctime)s - %(message)s", level=LoggingLevelService.get_level()
)
ConfigService.log_defined_env_vars()

cache_svc = CacheService({})
owl_info = None  # lazy-initialized
owl_xml = None  # lazy-initialized

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
    if graph_microsvc_sparql_query_url().startswith("http"):
        alive = True
    else:
        alive = False  # unable to reach the graph service due to url config

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
    logging.info("get_home")
    view_data = dict()
    return views.TemplateResponse(request=req, name="home.html", context=view_data)


@app.get("/about")
async def get_about(req: Request):
    view_data = dict()
    return views.TemplateResponse(request=req, name="about.html", context=view_data)


@app.get("/config")
async def get_config(req: Request):
    view_data = dict()
    return views.TemplateResponse(request=req, name="config.html", context=view_data)


@app.get("/sparql_console")
async def get_sparql_console(req: Request):
    if ConfigService.use_alt_sparql_console():
        view_data = get_alt_sparql_console(req)
        return views.TemplateResponse(
            request=req, name="alt_sparql_console.html", context=view_data
        )
    else:
        view_data = get_libraries_sparql_console(req)
        return views.TemplateResponse(
            request=req, name="sparql_console.html", context=view_data
        )


@app.post("/sparql_console")
async def post_sparql_console(req: Request):
    form_data = await req.form()  # <class 'starlette.datastructures.FormData'>
    if ConfigService.use_alt_sparql_console():
        view_data = post_alt_sparql_console(form_data)
        return views.TemplateResponse(
            request=req, name="alt_sparql_console.html", context=view_data
        )
    else:
        view_data = post_libraries_sparql_console(form_data)
        return views.TemplateResponse(
            request=req, name="sparql_console.html", context=view_data
        )


@app.get("/gen_sparql_console")
async def get_ai_console(req: Request):
    view_data = gen_sparql_console_view_data()
    view_data[
        "natural_language"
    ] = "What are the dependencies of the 'pypi' type of library named 'flask'?"
    view_data["sparql"] = "SELECT * WHERE { ?s ?p ?o . } LIMIT 10"
    return views.TemplateResponse(
        request=req, name="gen_sparql_console.html", context=view_data
    )


@app.post("/gen_sparql_console_generate_sparql")
async def ai_post_gen_sparql(req: Request):
    global owl_xml
    form_data = await req.form()
    logging.info(form_data)
    natural_language = form_data.get("natural_language")
    view_data = gen_sparql_console_view_data()
    view_data["natural_language"] = natural_language
    url = ai_gen_sparql_url()
    postdata = dict()
    postdata["session_id"] = str(uuid.uuid1())
    postdata["natural_language"] = natural_language
    postdata["owl"] = owl_xml
    r = httpx.post(url, data=json.dumps(postdata), timeout=120.0)
    resp_obj = json.loads(r.text)
    view_data["results"] = json.dumps(resp_obj, sort_keys=False, indent=2)
    view_data["results_message"] = "Generative AI Response"
    sparql = resp_obj["sparql"]
    view_data["sparql"] = SparqlFormatter().pretty(sparql)
    return views.TemplateResponse(
        request=req, name="gen_sparql_console.html", context=view_data
    )


@app.post("/gen_sparql_console_execute_sparql")
async def gen_sparql_console_execute_sparql(req: Request):
    form_data = await req.form()
    logging.info(form_data)
    view_data = gen_sparql_console_view_data()
    sparql = form_data.get("sparql")
    view_data["sparql"] = sparql

    resp_obj = post_sparql_query_to_graph_microsvc(sparql)
    view_data["results"] = json.dumps(resp_obj, sort_keys=False, indent=2)
    view_data["results_message"] = "SPARQL Query Results"
    return views.TemplateResponse(
        request=req, name="gen_sparql_console.html", context=view_data
    )


@app.get("/conv_ai_console")
async def conv_ai_console(req: Request):
    view_data = dict()
    # TODO - design UI and implement
    return views.TemplateResponse(
        request=req, name="conv_ai_console.html", context=view_data
    )


# non-endpoint methods:


def gen_sparql_console_view_data():
    """
    Lazy-initialize the various OWL content by first HTTP fetching it
    from the graph microservice.
    """
    global owl_xml
    global owl_info
    if owl_xml == None:
        logging.info(
            "lazy-initializing owl variables, calling the graph microservice..."
        )
        owl_info = get_graph_service_owl_info()
        owl_xml = owl_info["owl"]
        if owl_xml == None:
            logging.critical("owl_xml is None")
        else:
            logging.info("owl_xml length: {}".format(len(owl_xml)))
        logging.debug("owl_xml: {}".format(owl_xml))

    view_data = dict()
    view_data[
        "natural_language"
    ] = "What are the dependencies of the 'pypi' type of library named 'flask'?"
    view_data["sparql"] = ""
    view_data["owl"] = owl_xml
    view_data["results_message"] = ""
    view_data["results"] = ""
    return view_data


def graph_microsvc_owl_info_url():
    return "{}:{}/owl_info".format(
        ConfigService.graph_service_url(), ConfigService.graph_service_port()
    )


def graph_microsvc_sparql_query_url():
    return "{}:{}/sparql_query".format(
        ConfigService.graph_service_url(), ConfigService.graph_service_port()
    )


def graph_microsvc_bom_query_url():
    return "{}:{}/sparql_bom_query".format(
        ConfigService.graph_service_url(), ConfigService.graph_service_port()
    )


def ai_gen_sparql_url():
    return "{}:{}/gen_sparql_query".format(
        ConfigService.ai_service_url(), ConfigService.ai_service_port()
    )


# At this time the web application can support up to two different
# SPARQL console views, the libraries view and an alternative view.
# But the UI will show only one of these.
# The logic to handle these two cases is below.


def get_libraries_sparql_console(req: Request) -> dict:
    """Return the view data for the libraries SPARQL console"""
    sparql = """
PREFIX c: <http://cosmosdb.com/caig#> 
SELECT ?used_lib
WHERE {
    <http://cosmosdb.com/caig/pypi_flask> c:uses_lib ?used_lib .
}
LIMIT 10
"""
    view_data = dict()
    view_data["method"] = "get"
    view_data["sparql"] = sparql
    view_data["bom_query"] = ""
    view_data["results_message"] = ""
    view_data["results"] = ""
    view_data["bom_json_str"] = "{}"
    view_data["inline_bom_json"] = "{}"
    view_data["libtype"] = ""
    return view_data


def get_alt_sparql_console(req: Request):
    """Return the view data for the alternative SPARQL console"""
    sparql = """
SELECT * WHERE { ?s ?p ?o . } LIMIT 10
"""
    view_data = dict()
    view_data["method"] = "get"
    view_data["sparql"] = sparql
    view_data["results_message"] = ""
    view_data["results"] = ""
    return view_data


def post_libraries_sparql_console(form_data):
    global cache_svc
    sparql = form_data.get("sparql")
    bom_query = form_data.get("bom_query").strip()
    use_cache = form_data.get("use_cache")  # Will be None if checkbox not checked
    logging.info("sparql: {}".format(sparql))
    logging.info("bom_query: {}".format(bom_query))
    logging.info("use_cache: {}".format(use_cache))

    view_data = dict()
    view_data["method"] = "post"
    view_data["sparql"] = sparql
    view_data["bom_query"] = bom_query
    view_data["results_message"] = "Results"
    view_data["results"] = ""
    view_data["bom_json_str"] = "{}"
    view_data["inline_bom_json"] = "{}"
    view_data["libtype"] = ""

    # execute either a BOM query or a simple SPARQL query, per Form input

    if len(bom_query) > 0:
        tokens = bom_query.split()
        if len(tokens) == 3:
            view_data["libtype"] = tokens[0]
            cache_key = "_".join(tokens)
            logging.info("cache_key: {}".format(cache_key))
            bom_obj = None
            if use_cache is not None:
                t1 = time.perf_counter()
                bom_obj = cache_svc.get(cache_key)
                if bom_obj is not None:
                    t2 = time.perf_counter()
                    elapsed = t2 - t1
                    seconds = f"{(t2 - t1):.9f}"
                    bom_obj["elapsed"] = seconds
                    bom_obj["from_cache"] = True
                    remove_mongo_id_attr(bom_obj)
                logging.info("cache get for key: {} {}".format(cache_key, bom_obj))

            if bom_obj is None:
                url = graph_microsvc_bom_query_url()
                logging.info("url: {}".format(url))
                postdata = dict()
                postdata["libtype"] = tokens[0]
                postdata["libname"] = tokens[1]
                postdata["max_depth"] = tokens[2]
                logging.info("postdata: {}".format(postdata))
                r = httpx.post(url, data=json.dumps(postdata), timeout=120.0)
                bom_obj = json.loads(r.text)
                logging.info("setting cache key: {} {}".format(cache_key, bom_obj))
                cache_svc.set(cache_key, bom_obj)
                bom_obj["from_cache"] = False
                logging.info("cache set for key: {}".format(cache_key))
            else:
                logging.info("cache hit for key: {}".format(cache_key))

            view_data["results"] = json.dumps(bom_obj, sort_keys=False, indent=2)
            view_data["inline_bom_json"] = view_data["results"]
        else:
            view_data["results"] = "Invalid BOM query: {}".format(bom_query)
    else:
        response_obj = post_sparql_query_to_graph_microsvc(sparql)
        view_data["results"] = json.dumps(response_obj, sort_keys=False, indent=2)
    return view_data


def post_alt_sparql_console(form_data):
    sparql = form_data.get("sparql")
    view_data = dict()
    view_data["method"] = "post"
    view_data["sparql"] = sparql
    view_data["results_message"] = ""
    view_data["results"] = ""
    logging.info("sparql: {}".format(sparql))

    if len(sparql) > 0:
        response_obj = post_sparql_query_to_graph_microsvc(sparql)
        view_data["results"] = json.dumps(response_obj, sort_keys=False, indent=2)
    return view_data


def post_sparql_query_to_graph_microsvc(sparql: str) -> None:
    """
    Execute a HTTP POST to the graph microservice with the given SPARQL query.
    Return the HTTP response JSON object.
    """
    try:
        url = graph_microsvc_sparql_query_url()
        postdata = dict()
        postdata["sparql"] = sparql
        r = httpx.post(url, data=json.dumps(postdata), timeout=120.0)
        obj = json.loads(r.text)
        return obj
    except Exception as e:
        logging.critical((str(e)))
        logging.exception(e, stack_info=True, exc_info=True)
        return {}


def post_sparql_gen_request_to_ai_microservice(natural_language: str) -> None:
    """
    Execute a HTTP POST to the ai microservice to generate a SPARQL
    query from the given natural language.
    Return the HTTP response JSON object.
    """
    global owl_minimized
    try:
        url = graph_microsvc_sparql_query_url_url()
        postdata = dict()
        postdata["sparql"] = sparql
        r = httpx.post(url, data=json.dumps(postdata), timeout=120.0)
        obj = json.loads(r.text)
        return obj
    except Exception as e:
        logging.critical((str(e)))
        logging.exception(e, stack_info=True, exc_info=True)
        return {}


def get_graph_service_owl_info():
    global owl_info
    try:
        if owl_info == None:
            url = graph_microsvc_owl_info_url()
            r = httpx.get(url, timeout=10.0)
            obj = json.loads(r.text)
            owl_info = obj
    except Exception as e:
        logging.critical((str(e)))
        logging.exception(e, stack_info=True, exc_info=True)
    return owl_info


def remove_mongo_id_attr(mongo_doc) -> None:
    """
    Remove the '_id' attribute from the Mongo object because
    ObjectId values are not JSON serializable
    """
    if mongo_doc is not None:
        if "_id" in mongo_doc.keys():
            del mongo_doc["_id"]
