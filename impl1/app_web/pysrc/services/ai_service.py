import json
import logging
import os
import sys
import time
import traceback
import xmlformatter

from openai import AzureOpenAI

from pysrc.services.config_service import ConfigService

from pysrc.models.internal_models import SparqlGenerationResult

from pysrc.util.fs import FS
from pysrc.util.owl_formatter import OwlFormatter
from pysrc.util.sparql_formatter import SparqlFormatter
from pysrc.util.prompts import Prompts

# Instances of this class are used to execute AzureOpenAI and LangChain functionality.
# Chris Joakim, Aleksey Savateyev, Microsoft


class AiService:
    def __init__(self, opts={}):
        """
        Get the necessary environment variables and initialze an AzureOpenAI client.
        Also read the OWL file.
        """
        try:
            self.opts = opts
            self.endpoint = ConfigService.azure_openai_url()
            self.version = ConfigService.azure_openai_version()
            api_key = ConfigService.azure_openai_key()
            self.aoai_client = AzureOpenAI(
                azure_endpoint=self.endpoint, api_key=api_key, api_version=self.version
            )
            self.completions_deployment = (
                ConfigService.azure_openai_completions_deployment()
            )
            self.embeddings_deployment = (
                ConfigService.azure_openai_embeddings_deployment()
            )
            logging.info("endpoint:     {}".format(self.endpoint))
            logging.info("api_key:      {}".format(api_key))
            logging.info("version:      {}".format(self.version))
            logging.info("aoai_client:  {}".format(self.aoai_client))
            logging.info(
                "completions_deployment: {}".format(self.completions_deployment)
            )
            logging.info(
                "embeddings_deployment:  {}".format(self.embeddings_deployment)
            )
        except Exception as e:
            logging.critical("Exception in AiService#__init__: {}".format(str(e)))
            logging.exception(e, stack_info=True, exc_info=True)
            return None

    def generate_sparql_from_user_prompt(
        self, resp_obj: dict
    ) -> SparqlGenerationResult:
        try:
            user_prompt = resp_obj["natural_language"]
            raw_owl = resp_obj["owl"]
            owl = OwlFormatter().minimize(raw_owl)
            logging.info(
                "AiService#generate_sparql_from_user_prompt - user_prompt: {}".format(
                    user_prompt
                )
            )
            logging.info(
                "AiService#generate_sparql_from_user_prompt - owl first 80 chars: {}".format(
                    str(owl)[0:80]
                )
            )
            if self.moderate_sparql_gen_input(user_prompt, owl):
                t1 = time.perf_counter()
                system_prompt = Prompts().generate_sparql_system_prompt(owl)
                completion = self.aoai_client.chat.completions.create(
                    model=self.completions_deployment,
                    temperature=0,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                t2 = time.perf_counter()
                # completion is an instance of <class 'openai.types.chat.chat_completion.ChatCompletion'>
                # https://platform.openai.com/docs/api-reference/chat/object
                sparql = json.loads(completion.choices[0].message.content).get("SPARQL")
                resp_obj["completion_id"] = completion.id
                resp_obj["completion_model"] = completion.model
                resp_obj["prompt_tokens"] = completion.usage.prompt_tokens
                resp_obj["completion_tokens"] = completion.usage.completion_tokens
                resp_obj["total_tokens"] = completion.usage.total_tokens
                resp_obj["elapsed"] = t2 - t1
                resp_obj["sparql"] = sparql
                if resp_obj["sparql"] == None:
                    resp_obj["sparql"] = ""
                logging.info(
                    "AiService#generate_sparql_from_user_prompt - sparql: {}".format(
                        sparql
                    )
                )
            else:
                resp_obj["error"] = "content moderation failed"
        except Exception as e:
            resp_obj["error"] = str(e)
            logging.critical("Exception in create_sparql_query: {}".format(str(e)))
            logging.exception(e, stack_info=True, exc_info=True)
        return resp_obj

    def moderate_sparql_gen_input(self, user_prompt, owl):
        """Return True if the input should be processed, else return False."""
        try:
            if user_prompt == None:
                return False
            if owl == None:
                return False
            if len(user_prompt.strip()) < 10:
                return False
            if len(owl.strip()) < 10:
                return False
            return True
        except Exception as e:
            return False
