from xml.sax import make_parser

from pysrc.util.fs import FS
from pysrc.util.owl_sax_handler import OwlSaxHandler

# This class uses the raw parsed data from the OwlSaxHandler class
# and reformats it as a JSON data structure more suitable for D3.js.
# Chris Joakim, Microsoft


class OwlVisualizer:

    def __init__(self, owl_filename):
        self.parser = make_parser()
        self.handler = OwlSaxHandler()
        self.parser.setContentHandler(self.handler)
        self.parser.parse(owl_filename)
        FS.write_json(self.handler.get_data(), "tmp/owl_vizualizer.json")

    def get_d3_data(self):
        sax_data = self.handler.get_data()
        d3_data = dict()
        d3_data["classes"] = sorted(sax_data["classes"])
        d3_data["relationships"] = list()
        d3_data["attributes"] = list()

        for name in sorted(sax_data["object_properties"].keys()):
            p = sax_data["object_properties"][name]
            domain_list, range_list = p["domain"], p["range"]
            for domain in domain_list:
                for range in range_list:
                    if domain != range:
                        d3_data["relationships"].append(
                            {
                                "name": name,
                                "source": domain,
                                "target": range,
                                "weight": "1.0",
                            }
                        )

        for key in sorted(sax_data["datatype_properties"].keys()):
            p = sax_data["datatype_properties"][key]
            domain_list, range_list = p["domain"], p["range"]
            for domain in domain_list:
                for range in range_list:
                    if domain != range:
                        d3_data["attributes"].append(
                            {"name": key, "source": domain, "target": range}
                        )

        return d3_data
