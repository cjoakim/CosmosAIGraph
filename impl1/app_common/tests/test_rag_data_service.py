import json
import pytest

from pysrc.services.ai_completion import AiCompletion
from pysrc.services.ai_conversation import AiConversation
from pysrc.services.ai_service import AiService
from pysrc.services.cosmos_vcore_service import CosmosVCoreService
from pysrc.services.config_service import ConfigService
from pysrc.services.rag_data_service import RAGDataService
from pysrc.services.strategy_builder import StrategyBuilder
from pysrc.services.rag_data_result import RAGDataResult
from pysrc.util.fs import FS

# pytest tests/test_rag_data_service.py
# del tmp/*.* ; pytest tests/test_rag_data_service.py

@pytest.mark.asyncio
async def test_get_database_rag_data():
    ConfigService.set_standard_unit_test_env_vars()
    opts = dict()
    opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
    ai_svc = AiService()
    vcore = CosmosVCoreService(opts)
    rds = RAGDataService(ai_svc, vcore)

    ai_svc = AiService()
    sb = StrategyBuilder(ai_svc)
    user_text = "lookup PyPi Flask"
    strategy_obj = await sb.determine(user_text)
    assert strategy_obj["strategy"] == "db"

    rdr: RAGDataResult = await rds.get_rag_data(user_text, 7)
    FS.write_json(rdr.get_data(), "tmp/test_get_database_rag_data.json")
    text = rdr.as_system_prompt_text()
    FS.write("tmp/test_get_database_rag_data.txt", text)

    assert rdr.get_strategy() == "db"
    assert rdr.get_data()["libtype"] == "pypi"
    assert rdr.get_data()["name"] == "flask"


@pytest.mark.asyncio
async def test_get_vector_rag_data():
    ConfigService.set_standard_unit_test_env_vars()
    opts = dict()
    opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
    ai_svc = AiService()
    vcore = CosmosVCoreService(opts)
    rds = RAGDataService(ai_svc, vcore)

    ai_svc = AiService()
    sb = StrategyBuilder(ai_svc)
    user_text = "what is the purpose of the Python pydantic library"
    strategy_obj = await sb.determine(user_text)
    assert strategy_obj["strategy"] == "vector"

    rdr: RAGDataResult = await rds.get_rag_data(user_text, 5)
    FS.write_json(rdr.get_data(), "tmp/test_get_vector_rag_data.json")
    text = rdr.as_system_prompt_text()
    FS.write("tmp/test_get_vector_rag_data.txt", text)

@pytest.mark.asyncio
async def test_get_graph_rag_data():
    ConfigService.set_standard_unit_test_env_vars()
    opts = dict()
    opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
    ai_svc = AiService()
    vcore = CosmosVCoreService(opts)
    rds = RAGDataService(ai_svc, vcore)
    ai_svc = AiService()
    sb = StrategyBuilder(ai_svc)
    user_text = "What are the dependencies of the 'pypi' type of library named 'flask'?"
    strategy_obj = await sb.determine(user_text)
    assert strategy_obj["strategy"] == "graph"

    rdr: RAGDataResult = await rds.get_rag_data(user_text,5)
    FS.write_json(rdr.get_data(),"tmp/test_get_graph_rag_data.json")
    text = rdr.as_system_prompt_text()
    FS.write("tmp/test_get_graph_rag_data.txt", text)
