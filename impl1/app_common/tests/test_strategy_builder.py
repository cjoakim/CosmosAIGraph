import pytest

from pysrc.services.ai_service import AiService
from pysrc.services.strategy_builder import StrategyBuilder
from pysrc.util.fs import FS

# pytest tests/test_strategy_builder.py

@pytest.mark.asyncio
async def test_determine():
    ai_svc = AiService()
    sb = StrategyBuilder(ai_svc)
    examples_list = FS.read_json(
        "../data/testdata/strategy_builder_examples.json")

    assert len(examples_list) > 5

    for example in examples_list:
        natural_language = example["natural_language"]
        expected_strategy = example["strategy"]
        strategy_obj = await sb.determine(natural_language)
        print("example: {}\nstrategy_obj: {}".format(example, strategy_obj))
        assert strategy_obj["natural_language"] == natural_language
        assert strategy_obj["strategy"] == expected_strategy
    