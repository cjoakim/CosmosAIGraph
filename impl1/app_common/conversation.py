"""
This module is for ad-hoc development and testing of "conversational ai"
functionality outside of the UI.
Usage:
    python conversation.py conv1
    python conversation.py conv2 > tmp/conv2.txt
    python conversation.py summarize
Options:
  -h --help     Show this screen.
  --version     Show version.
"""

import asyncio
import json
import logging
import sys
import time

from docopt import docopt
from dotenv import load_dotenv

# Services with Business Logic
from pysrc.services.ai_completion import AiCompletion
from pysrc.services.ai_conversation import AiConversation
from pysrc.services.ai_service import AiService
from pysrc.services.config_service import ConfigService
from pysrc.services.cosmos_vcore_service import CosmosVCoreService
from pysrc.services.logging_level_service import LoggingLevelService
from pysrc.util.fs import FS
from pysrc.util.sparql_formatter import SparqlFormatter
from pysrc.services.ontology_service import OntologyService
from pysrc.services.rag_data_service import RAGDataService
from pysrc.services.rag_strategy_builder import RAGStrategyBuilder
from pysrc.services.rag_data_result import RAGDataResult

logging.basicConfig(
    format="%(asctime)s - %(message)s", level=LoggingLevelService.get_level()
)


def print_options(msg):
    print(msg)
    arguments = docopt(__doc__, version="1.0.0")
    print(arguments)


async def conv1():
    """This is a simple 'RAGless' conversation that doesn't use the library data"""
    logging.info("conv1")
    load_dotenv(override=True)
    logging.basicConfig(
        format="%(asctime)s - %(message)s", level=LoggingLevelService.get_level()
    )
    ConfigService.log_defined_env_vars()

    # setup the various services used in the conversation
    ai_svc = AiService()
    ontology_svc = OntologyService()
    owl_xml = ontology_svc.get_owl_content()
    logging.info("owl_xml:\n{}".format(owl_xml))
    vcore_opts = dict()
    vcore_opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
    logging.info("vcore_opts: {}".format(vcore_opts))
    vcore = CosmosVCoreService(vcore_opts)
    vcore.set_db(ConfigService.graph_source_db())
    rds = RAGDataService(ai_svc, vcore)
    conversation_id = "test-conv-{}".format(int(time.time()))
    outfile = "tmp/{}.json".format(conversation_id)
    sleep_seconds = 3.0

    # start the conversation
    conv = vcore.load_conversation(
        conversation_id
    )  # returns a new or existing conversation
    logging.warning("load_conversation: {} {}".format(conv, conv.serialize()))
    conv.conversation_id = conversation_id
    vcore.save_conversation(conv)
    logging.warning("new conversation saved: {}".format(conversation_id))

    user_queries = [
        "who invented the telephone",
        "when was he born",
        "what other three historic events happened that year",
    ]
    context = ""

    for user_query in user_queries:
        print("====================================")
        logging.info("user_query: {}".format(user_query))
        conv.add_user_message(user_query)
        prompt_text = ai_svc.generic_prompt()
        completion: AiCompletion = await ai_svc.invoke_kernel(
            conv, prompt_text, user_query, context=context
        )
        context = completion.get_content()
        vcore.save_conversation(conv)
        FS.write_json(json.loads(conv.serialize()), outfile)
        time.sleep(sleep_seconds)

    print("mongosh lookup command for Cosmos DB vCore:")
    print("db.conversations.find({conversation_id: '" + conversation_id + "'})")
    conv.print_summary()


async def conv2():
    """This is a RAG-based conversation that uses the library data"""
    logging.info("conv1")
    load_dotenv(override=True)
    logging.basicConfig(
        format="%(asctime)s - %(message)s", level=LoggingLevelService.get_level()
    )
    ConfigService.log_defined_env_vars()

    # setup the various services used in the conversation
    ai_svc = AiService()
    ontology_svc = OntologyService()
    owl_xml = ontology_svc.get_owl_content()
    logging.info("owl_xml:\n{}".format(owl_xml))
    vcore_opts = dict()
    vcore_opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
    logging.info("vcore_opts: {}".format(vcore_opts))
    vcore = CosmosVCoreService(vcore_opts)
    vcore.set_db(ConfigService.graph_source_db())
    rds = RAGDataService(ai_svc, vcore)
    conversation_id = "test-conv-{}".format(int(time.time()))
    outfile = "tmp/{}.json".format(conversation_id)
    sleep_seconds = 5.0

    # start the conversation
    conv = vcore.load_conversation(conversation_id)
    conv.conversation_id = conversation_id
    vcore.save_conversation(conv)
    logging.warning("new conversation saved: {}".format(conversation_id))

    user_queries = [
        "pypi flask library",
        "what is the flask library",
        "what are the top two asynchronous alternatives to it",
        "which uses pydantic",
        "what is its dependency graph",
        "dependencies of the pypi Flask lib",
    ]

    for user_query in user_queries:
        logging.info("user_query: {}".format(user_query))
        conv.add_user_message(user_query)
        prompt_text = ai_svc.generic_prompt()

        last_completion_content = conv.last_completion_content()
        rdr: RAGDataResult = await rds.get_rag_data(user_query, 1)

        context = "{}\n{}".format(
            conv.last_completion_content(), rdr.get_rag_data_json()
        )

        print(">>>>>>>>>>")
        print(json.dumps(context, sort_keys=False, indent=2))
        print("<<<<<<<<<<")

        completion: AiCompletion = await ai_svc.invoke_kernel(
            conv, prompt_text, user_query, context=context
        )
        completion.set_rag_strategy(rdr.get_strategy())

        if completion is None:
            logging.error("completion is None")
            continue
        else:
            # print("completion content: {}".format(completion.get_content()))
            context = completion.get_content()
            vcore.save_conversation(conv)
            FS.write_json(json.loads(conv.serialize()), outfile)
        print("sleeping for {} seconds".format(sleep_seconds))
        time.sleep(sleep_seconds)

    print("mongosh lookup command for Cosmos DB vCore:")
    print("db.conversations.find({conversation_id: '" + conversation_id + "'})")


async def summarize():
    ai_svc = AiService()
    infile = "../data/pypi/html_pages/pypi_pydantic_27464.json"
    data = FS.read_json(infile)
    html = data["html"]
    for n in range(0, 3):
        print("==========")
        print("{} html: \n{}".format(n, html))
        output = await ai_svc.summarize_html(html)
        print("\n---\noutput: \n{}".format(output))


if __name__ == "__main__":
    load_dotenv(override=True)

    if len(sys.argv) < 2:
        print_options("Error: invalid command-line")
        exit(1)
    else:
        try:
            func = sys.argv[1].lower()
            if func == "conv1":
                asyncio.run(conv1())
            elif func == "conv2":
                asyncio.run(conv2())
            elif func == "summarize":
                asyncio.run(summarize())
            else:
                print_options("Error: invalid function: {}".format(func))
        except Exception as e:
            logging.critical(str(e))
            logging.exception(e, stack_info=True, exc_info=True)
