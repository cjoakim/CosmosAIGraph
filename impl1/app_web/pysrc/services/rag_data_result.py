import json
import time

# Instances of this class are used as the data structure that is returned
# from the RagDataService get_rag_docs() method.  This result object is
# useful to the UI to explain the actions and processing of the application.
# Chris Joakim, Microsoft


class RAGDataResult:

    def __init__(self):
        self.data = dict()
        self.data["type"] = "RAGDataResult"
        self.data["user_text"] = ""
        self.data["strategy"] = list()
        self.data["sparql"] = ""
        self.data["rag_docs"] = list()
        self.data["rag_doc_count"] = -1

    def finish(self):
        self.data["rag_doc_count"] = len(self.data["rag_docs"])

    def set_attr(self, attr_name, value):
        if attr_name is not None:
            if value is not None:
                self.data[attr_name] = value

    def get_data(self):
        return self.data

    def get_rag_docs(self):
        return self.data["rag_docs"]

    def add_doc(self, doc):
        self.data["rag_docs"].append(doc)

    def get_strategy(self):
        return ",".join(self.data["strategy"])

    def set_user_text(self, value):
        if value is not None:
            self.data["user_text"] = str(value)

    def set_sparql(self, value):
        if value is not None:
            self.data["sparql"] = str(value)

    def get_sparql(self):
        return self.data["sparql"]

    def set_rag_docs(self, value):
        if value is not None:
            self.data["rag_docs"] = value

    def add_strategy(self, value):
        if value is not None:
            self.data["strategy"].append(str(value))

    def as_system_prompt_text(self):
        prompt_lines = list()
        docs = self.data["rag_docs"]
        if len(docs) > 0:
            prompt_lines.append(
                "Use these {} Documents to answer the user query:".format(len(docs))
            )
            prompt_lines.append(
                "Each document has a library name and type, summary, and documentation."
            )

        for doc in self.data["rag_docs"]:
            prompt_lines.append("\nDocument:")
            prompt_lines.append(
                "library name: {} type: {}".format(doc["name"], doc["libtype"])
            )
            prompt_lines.append("summary: {}".format(doc["summary"]))
            prompt_lines.append(
                "documentation:\n{}".format(doc["documentation_summary"])
            )
        return "\n".join(prompt_lines)
