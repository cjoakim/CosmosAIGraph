import traceback

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

# This class uses the xml.sax standard-library to parse a given
# OWL ontology file and identify its classes and properties.
# See https://docs.python.org/3/library/xml.sax.handler.html
#
# The output from parsing an OWL file is a JSON data structure
# that can be useful for analyzing or visualizing the ontology,
# such as with D3.js in a Web browser.
#
# Chris Joakim, Microsoft


class OwlSaxHandler(ContentHandler):

    def __init__(self):
        self.xmlns = ""
        self.classes = dict()
        self.properties = dict()
        self.curr_tag = ""
        self.curr_object_property = dict()
        self.in_class = False
        self.in_object_property = False

    def get_data(self):
        data = dict()
        data["xmlns"] = self.xmlns
        data["classes"] = self.classes
        data["properties"] = self.properties
        return data

    def set_namespace(self, attrs):
        attr_names = attrs.keys()
        if "xmlns" in attr_names:
            self.xmlns = attrs.getValue("xmlns")

    def add_class(self, name, attrs):
        try:
            attr_names = attrs.keys()
            if "rdf:ID" in attr_names:
                name = attrs.getValue("rdf:ID")
                self.classes[name] = dict()
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def add_object_property(self, name, attrs):
        try:
            self.in_object_property = True
            self.curr_object_property = dict()
            self.curr_object_property["domain"] = list()
            self.curr_object_property["range"] = list()
            attr_names = attrs.keys()
            name = "?"
            if "rdf:ID" in attr_names:
                name = attrs.getValue("rdf:ID")
            self.curr_object_property["name"] = name
            self.properties[name] = self.curr_object_property
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def add_object_property_domain(self, attrs):
        try:
            attr_names = attrs.keys()
            if "rdf:resource" in attr_names:
                value = attrs.getValue("rdf:resource").replace("#", "")
                self.curr_object_property["domain"].append(value)
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def add_object_property_range(self, attrs):
        try:
            attr_names = attrs.keys()
            if "rdf:resource" in attr_names:
                value = attrs.getValue("rdf:resource").replace("#", "")
                self.curr_object_property["range"].append(value)
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def end_object_property(self):
        try:
            is_edge = True  # assume True
            for value in self.curr_object_property["domain"]:
                if "http://" in value:  # "http://www.w3.org/2001/XMLSchema#string"
                    is_edge = False
            for value in self.curr_object_property["range"]:
                if "http://" in value:  # "http://www.w3.org/2001/XMLSchema#string"
                    is_edge = False
            self.curr_object_property["is_edge"] = is_edge

        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    # Application logic above; ContentHandler methods below

    def startDocument(self):
        try:
            print("startDocument")
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def endDocument(self):
        try:
            print("endDocument")
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def startPrefixMapping(prefix, uri):
        try:
            print("startPrefixMapping; prefix: {} uri: {}".format(prefix, uri))
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def endPrefixMapping(prefix):
        try:
            print("endPrefixMapping; prefix: {}".format(prefix))
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def startElement(self, name, attrs):
        # attrs is an instance of xml.sax.xmlreader.AttributesImpl
        try:
            self.curr_tag = name
            attr_names = attrs.keys()
            ad = self.attributes_dict(attrs)
            print("startElement: {} {}".format(name, ad))

            if "rdf:RDF" == name:
                self.set_namespace(attrs)
            elif "owl:Class" == name:
                self.in_class = True
                self.add_class(name, attrs)
            elif "owl:ObjectProperty" == name:
                self.add_object_property(name, attrs)
            elif "rdfs:domain" == name:
                if self.in_object_property:
                    self.add_object_property_domain(attrs)
            elif "rdfs:range" == name:
                if self.in_object_property:
                    self.add_object_property_range(attrs)

        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def endElement(self, name):
        try:
            print("endElement: {}".format(name))
            if "owl:Class" == name:
                self.in_class = False
            elif "owl:ObjectProperty" == name:
                self.in_object_property = False
                self.end_object_property()

        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def startElementNS(self, name, qname, attrs):
        try:
            print("startElementNS: {} {} {}".format(name, qname, sorted(attrs.keys())))
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def endElementNS(self, name, qname):
        try:
            print("endElementNS: {} {}".format(name, qname))
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def characters(self, content):
        try:
            print("characters: {}".format(str(content)))
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def ignorableWhitespace(self, ws):
        pass

    def processingInstruction(self, target, data):
        pass

    def skippedEntity(self, name):
        try:
            print("skippedEntity: {}".format(name))
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())

    def attributes_dict(self, attrs):
        attr_dict = dict()
        try:
            for attr_name in sorted(attrs.getNames()):
                attr_dict[attr_name] = attrs.getValue(attr_name)
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())
        return attr_dict
