import logging

from pysrc.models.internal_models import RAGStrategy
from pysrc.services.entities_service import EntitiesService

# CosmosAIGraph demonstrates "HybridRAG" search - graph, db, or vector -
# rather than just a single RAG data pattern.
#
# Instances of this class determine the intent of a user natural language
# query and infers from it the "strategy" to be used to obtain the
# appropriate data for the RAG pattern.  The three strategies are:
# 'graph_search', 'db_search', and 'vector_search'
#
# See the unit tests in file tests/test_rag_strategy_builder.py for example
# natural language statements and the resulting "strategy" to be applied.
#
# Chris Joakim, Microsoft


class RAGStrategyBuilder:

    def __init__(self):
        self.entities_svc = EntitiesService()
        self.entities_svc.initialize()

    def determine(self, natural_language) -> dict:
        strategy = dict()
        strategy["natural_language"] = natural_language
        strategy["strategy"] = (
            "vector_search"  # db_search, graph_search, or vector_search
        )
        strategy["libtype"] = "pypi"
        strategy["name"] = self.entities_svc.identify(natural_language).most_frequent()
        try:
            tokens = natural_language.lower().strip().split()
            strategy["tokens"] = tokens
            if len(tokens) < 6:
                for libtype in ["pypi", "python"]:
                    if self.db_search_match(libtype, tokens, strategy["name"]):
                        strategy["strategy"] = "db_search"
                        return strategy
            if self.graph_search_match(tokens) is True:
                strategy["strategy"] = "graph_search"
            else:
                strategy["strategy"] = "vector_search"
        except Exception as e:
            logging.critical(
                "Exception in RAGStrategyBuilder#determine: {} {}".format(
                    natural_language, str(e)
                )
            )
        return strategy

    def db_search_match(self, libtype, tokens, name):
        if name is not None and name != "":
            if libtype in tokens:
                for verb in "lookup,find,get".split(","):
                    if verb in tokens:
                        return True
        return False

    def graph_search_match(self, tokens) -> bool:
        if self.tokens_contains(["dependencies", "of"], tokens):
            return True
        if self.tokens_contains(["author", "of"], tokens):
            return True
        if self.tokens_contains(["authors", "of"], tokens):
            return True
        if self.tokens_contains(["developer", "of"], tokens):
            return True
        if self.tokens_contains(["developers", "of"], tokens):
            return True
        if self.tokens_contains(["bill", "of", "materials"], tokens):
            return True
        if self.tokens_contains(["graph", "of"], tokens):
            return True
        return False

    def tokens_contains(self, match_words, tokens) -> bool:
        matched_count = 0
        for word in match_words:
            if word in tokens:
                matched_count = matched_count + 1
        if matched_count == len(match_words):
            return True
        else:
            return False
