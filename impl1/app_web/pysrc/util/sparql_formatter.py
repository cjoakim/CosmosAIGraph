import jinja2
import logging
import psutil

# Instances of this class are used to return 'pretty' version of
# a given (AI-generated) SPARQL query.
# Chris Joakim, Microsoft


class SparqlFormatter:
    def __init__(self, opts={}):
        self.opts = opts

    def pretty(self, sparql: str) -> str:
        try:
            words, buffer, prev_word = sparql.split(), list(), ""
            for word in words:
                if word in ["PREFIX", "SELECT", "WHERE"]:
                    buffer.append("\n")
                    buffer.append(word)
                    buffer.append(" ")
                elif word in ["OPTIONAL"]:
                    # buffer.append("\n")
                    buffer.append(word)
                    buffer.append(" ")
                elif word in ["."]:
                    buffer.append(word)
                    buffer.append(" ")
                    buffer.append("\n    ")
                elif word in ["{"]:
                    if prev_word == "WHERE":
                        buffer.append(word)
                        buffer.append(" ")
                        buffer.append("\n    ")
                    else:
                        buffer.append(word)
                        buffer.append(" ")
                else:
                    buffer.append(word)
                    buffer.append(" ")
                prev_word = word
            joined = "".join(buffer).strip()
            return joined.replace("    }", "}").replace("} }", "}}")
        except Exception as e:
            logging.critical("Exception in pretty_sparql: {}".format(str(e)))
            logging.exception(e, stack_info=True, exc_info=True)
            return sparql
