# This is the entry-point for this microservice, built with the
# FastAPI web framework
#
# Chris Joakim, Microsoft

import json
import logging
import time
import traceback

from dotenv import load_dotenv

from fastapi import FastAPI, Request, Response, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Pydantic models defining the "shapes" of requests and responses
from pysrc.models.webservice_models import PingModel
from pysrc.models.webservice_models import LivenessModel
from pysrc.models.webservice_models import SparqlGenerationRequestModel
from pysrc.models.webservice_models import SparqlGenerationResponseModel

# Services with Business Logic
from pysrc.services.ai_service import AiService
from pysrc.services.config_service import ConfigService
from pysrc.services.cosmos_vcore_service import CosmosVCoreService
from pysrc.services.logging_level_service import LoggingLevelService
from pysrc.util.fs import FS

# standard initialization
load_dotenv(override=True)
logging.basicConfig(
    format="%(asctime)s - %(message)s", level=LoggingLevelService.get_level()
)
ConfigService.log_defined_env_vars()

app = FastAPI()
ai_svc = AiService()


@app.get("/")
async def get_index() -> PingModel:
    resp = dict()
    resp["epoch"] = str(time.time())
    return resp


@app.get("/liveness")
async def get_liveness(req: Request, resp: Response) -> LivenessModel:
    """
    Return a LivenessModel indicating the health of this web app.
    This endpoint is invoked by the Azure Container Apps (ACA) service.
    """
    alive = True
    # TODO - implement liveness logic here
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


@app.post("/gen_sparql_query")
async def post_gen_sparql_query(
    req_model: SparqlGenerationRequestModel,
) -> SparqlGenerationResponseModel:
    global ai_svc
    resp_obj = dict()
    resp_obj["session_id"] = req_model.session_id
    resp_obj["natural_language"] = req_model.natural_language
    resp_obj["owl"] = req_model.owl
    resp_obj["completion_id"] = ""
    resp_obj["completion_model"] = ""
    resp_obj["prompt_tokens"] = -1
    resp_obj["completion_tokens"] = -1
    resp_obj["total_tokens"] = -1
    resp_obj["sparql"] = ""
    resp_obj["error"] = ""

    t1 = time.perf_counter()
    try:
        resp_obj = ai_svc.generate_sparql_from_user_prompt(resp_obj)
    except Exception as e:
        resp_obj["error"] = str(e)
        logging.critical((str(e)))
        logging.exception(e, stack_info=True, exc_info=True)

    resp_obj["epoch"] = int(time.time())
    resp_obj["elapsed"] = time.perf_counter() - t1
    logging.debug("post_gen_sparql_query: {}".format(json.dumps(resp_obj)))
    return resp_obj
