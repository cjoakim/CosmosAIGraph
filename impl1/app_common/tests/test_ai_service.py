import json
import os
import time
import pytest

from pysrc.services.ai_completion import AiCompletion
from pysrc.services.ai_conversation import AiConversation
from pysrc.services.ai_service import AiService
from pysrc.util.sparql_formatter import SparqlFormatter
from pysrc.util.fs import FS

# pytest tests/test_ai_service.py


def test_constructor():
    ai_svc = AiService()
    assert ai_svc.aoai_endpoint.startswith("https://")
    assert ai_svc.aoai_endpoint.endswith(".openai.azure.com/")
    assert ai_svc.aoai_version.startswith("2023-")
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
    print(result_obj)
    FS.write_json(result_obj, "tmp/test_generate_sparql_from_user_prompt.json")
    assert result_obj["prompt_tokens"] > 1000
    assert result_obj["prompt_tokens"] < 2000
    assert result_obj["completion_tokens"] > 30
    assert result_obj["completion_tokens"] < 130
    assert result_obj["total_tokens"] > 1000
    assert result_obj["total_tokens"] < 2000
    assert result_obj["elapsed"] > 0.001

    sf = SparqlFormatter()
    sparql = result_obj["sparql"]
    pretty = SparqlFormatter().pretty(sparql)
    assert 'http://cosmosdb.com/caig#' in pretty
    print(pretty)

def test_generate_embeddings():
    ai_svc = AiService()
    resp = ai_svc.generate_embeddings("python fastapi pydantic microservices")
    print(resp)
    assert resp is not None
    assert "CreateEmbeddingResponse" in str(type(resp)) 
    assert len(resp.data[0].embedding) == 1536

# @pytest.mark.skip(reason="this test is slow and exploratory, bypass for now")
# @pytest.mark.asyncio
# async def test_invoke_kernel():
#     ai_svc = AiService()
#     conversation = AiConversation()
#     conversation.add_system_message("You are a helpful chatbot.")

#     prompt_text = ai_svc.generic_prompt()
#     user_query = "who invented the telephone"
#     context = ""
#     completion1: AiCompletion = await ai_svc.invoke_kernel(
#         conversation, prompt_text, user_query, context)
#     print("completion 1 content: {}".format(completion1.get_content()))

#     if True:
#         prompt_text = ai_svc.generic_prompt()
#         user_query = "when was he born"
#         context = completion1.get_content()
#         completion2: AiCompletion = await ai_svc.invoke_kernel(
#             conversation, prompt_text, user_query, context, temperature=2.0)
#         print("completion 2 content: {}".format(completion2.get_content()))

#     if True:
#         prompt_text = ai_svc.generic_prompt()
#         user_query = "what other historic events happened that year"
#         context = completion2.get_content()
#         completion3: AiCompletion = await ai_svc.invoke_kernel(
#             conversation, prompt_text, user_query, context, temperature=2.0)
#         print("completion 3 content: {}".format(completion3.get_content()))

#     print('---')
#     print(conversation.serialize())
#     FS.write("tmp/test_invoke_kernel.json", conversation.serialize())

#     assert "alexander graham bell" in completion1.get_content().lower()
#     assert "1847" in completion2.get_content()
