import json

from pysrc.services.rag_strategy_builder import RAGStrategyBuilder
from pysrc.util.fs import FS

# pytest tests/test_rag_strategy_builder.py


def test_determine():
    rsb = RAGStrategyBuilder()
    examples_list = FS.read_json(
        "../data/testdata/rag_strategy_builder_examples.json")

    assert len(examples_list) > 5

    for example in examples_list:
        natural_language = example["natural_language"]
        expected_strategy = example["strategy"]
        expected_libtype = example["libtype"]
        expected_name = example["name"]
        strategy_obj = rsb.determine(natural_language)
        print("example: {}\nstrategy_obj: {}".format(example, strategy_obj))
        assert strategy_obj["natural_language"] == natural_language
        assert strategy_obj["strategy"] == expected_strategy
        assert strategy_obj["libtype"] == expected_libtype
        assert strategy_obj["name"] == expected_name
    