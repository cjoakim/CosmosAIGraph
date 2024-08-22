import datetime
import logging
import time

from src.services.config_service import ConfigService
from src.services.cosmos_vcore_service import CosmosVCoreService
from src.util.counter import Counter

# Instances of this class are used to:
# - create and populate the 'entities' document in Cosmos DB
# - identify known entities in given text data per the 'entities' document
# Chris Joakim, Microsoft


class EntitiesService:

    def __init__(self, vcore=None):
        """Constructor method, connect to Cosmos DB vcore"""
        self.vcore = None
        self.entities_doc = None
        self.libraries_dict = dict()
        self.library_names = list()
        try:
            if vcore is not None:
                self.vcore = vcore
            else:
                vcore_opts = dict()
                vcore_opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
                logging.debug(
                    "EntitiesService#init - vcore_opts: {}".format(vcore_opts)
                )
                self.vcore = CosmosVCoreService(vcore_opts)
            self.vcore.set_db(ConfigService.graph_source_db())
            self.vcore.set_coll(ConfigService.config_container())
        except Exception as e:
            logging.critical("EntitiesService#init - exception: {}".format(str(e)))
            logging.exception(e, stack_info=True, exc_info=True)

    def initialize(self):
        """Load the 'entities' document from Cosmos DB into this instance"""
        try:
            self.vcore.set_db(ConfigService.graph_source_db())
            self.vcore.set_coll(ConfigService.config_container())
            query_spec = {"id": "entities"}
            cursor = self.vcore.get_coll().find(query_spec, skip=0, limit=999999)
            docs_found = 0
            for result_doc in cursor:
                docs_found = docs_found + 1
                self.entities_doc = result_doc
                self.libraries_dict = result_doc["libraries"]
                if "pypi" in self.libraries_dict.keys():
                    del self.libraries_dict["pypi"]
                self.library_names = self.libraries_dict.keys()
            logging.warning(
                "EntitiesService#load - entities docs found: {}, size: {}".format(
                    docs_found, len(self.libraries_dict.keys())
                )
            )
        except Exception as e:
            self.libraries_dict = dict()
            logging.critical("EntitiesService#load - exception: {}".format(str(e)))
            logging.exception(e, stack_info=True, exc_info=True)

    def libraries_count(self):
        try:
            return len(self.libraries_dict.keys())
        except Exception as e:
            return -1

    def library_present(self, name):
        try:
            return name in self.library_names
        except Exception as e:
            pass
        return False

    def identify(self, text) -> Counter:
        """Identify the known entities in the given text data, return a dict"""
        c = Counter()
        if text is not None:
            words = text.lower().replace(",", " ").replace(".", " ").strip().split()
            for word in words:
                if len(word) > 1:
                    if word in self.library_names:
                        c.increment(word)
        return c

    def create(self):
        """Create and return the 'entities' document from the Cosmos DB library documents"""
        new_entities = dict()
        new_entities["id"] = "entities"
        new_entities["created_at"] = time.time()
        new_entities["created_date"] = str(
            datetime.datetime.fromtimestamp(new_entities["created_at"])
        )
        new_entities["docs_read"] = -1
        new_entities["elapsed_seconds"] = -1
        new_entities["exception"] = ""
        new_entities["libraries"] = dict()

        try:
            self.vcore.set_coll(ConfigService.graph_source_container())
            docs_read = 0
            logging.info("EntitiesService#build start")
            t1 = time.perf_counter()
            coll = self.vcore.get_coll()
            for libtype in ["pypi"]:
                query_spec = {"libtype": libtype}
                projection = self.library_projection_attrs()
                cursor = coll.find(
                    query_spec, projection=projection, skip=0, limit=999999
                )
                for libdoc in cursor:
                    docs_read = docs_read + 1
                    if docs_read % 1000 == 0:
                        logging.info(
                            "EntitiesService#build - libdocs read: {}".format(docs_read)
                        )
                    name = libdoc["name"]
                    new_entities["libraries"][name] = libdoc["libtype"]
            t2 = time.perf_counter()
            seconds = f"{(t2 - t1):.9f}"
            logging.critical(
                "EntitiesService#build - {} docs read in {} seconds".format(
                    docs_read, seconds
                )
            )
            new_entities["docs_read"] = docs_read
            new_entities["elapsed_seconds"] = seconds
        except Exception as e:
            new_entities["exception"] = str(e)
            logging.critical("EntitiesService#build - exception: {}".format(str(e)))
            logging.exception(e, stack_info=True, exc_info=True)
        return new_entities

    def library_projection_attrs(self):
        return {
            "name": 1,
            "libtype": 1,
            "developers": 1,
        }
