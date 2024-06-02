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

    examples_count = len(examples_list)
    assert examples_count > 5

    success_count = 0
    min_success_count = examples_count - 1
    # TODO - make 100% of test cases pass

    for example in examples_list:
        natural_language = example["natural_language"]
        expected_strategy = example["strategy"]
        strategy_obj = await sb.determine(natural_language)
        print("example: {}\nstrategy_obj: {}".format(example, strategy_obj))
        if strategy_obj["strategy"] == expected_strategy:
            success_count = success_count + 1
    assert success_count >= min_success_count
    