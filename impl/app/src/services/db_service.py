import asyncio
import logging

from src.services.config_service import ConfigService
from src.services.cosmos_nosql_service import CosmosNoSQLService
from src.services.cosmos_vcore_service import CosmosVCoreService

# Instances of this class are a wrapper for one of several possible underlying databases,
# including:
# 1) Cosmos DB Mongo vCore API
# 2) Cosmos DB NoSQL API
# 3) Azure PostgreSQL (future implementation)
# All methods are asynchronous for consistency between NoSQL (async) and vCore (sync).
# Chris Joakim, Microsoft


class DBService:
    
    def __init__(self, override_graph_source=None):
        """ Constructor method. """
        try:
            self.graph_source = ConfigService.graph_source()
            if override_graph_source is not None:
                self.graph_source = override_graph_source  # used for testing & unit tests
            self.vcore_svc  = None
            self.nosql_svc = None
            self.nosql_dbproxy = None
            self.nosql_ctrproxy = None
            self.dbname = None
            logging.info("DBService constructor complete; source: {}".format(self.graph_source))
        except Exception as e:
            logging.critical((str(e)))
            logging.exception(e, stack_info=True, exc_info=True)

    async def initialize(self):
        """ This method should be called immediately after the constructor. """
        if self.graph_source == "cosmos_nosql":
            await self.initialize_cosmos_nosql()
        else :
            await self.initialize_cosmos_vcore()

    async def initialize_cosmos_nosql(self):
        opts = dict()
        opts["enable_diagnostics_logging"] = False
        self.nosql_svc = CosmosNoSQLService(opts)
        await self.nosql_svc.initialize()
        dbname = ConfigService.graph_source_db()
        self.nosql_dbproxy = self.nosql_svc.set_db(dbname)

    async def initialize_cosmos_vcore(self):
        await asyncio.sleep(0.01)
        opts = dict()
        opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
        self.vcore_svc = CosmosVCoreService(opts)

    def set_db(self, dbname):
        logging.info("DBService#set_db: {}".format(dbname))
        self.dbname = dbname
        if self.graph_source == "cosmos_nosql":
            self.nosql_svc.set_db(dbname)
        else :
            self.vcore_svc.set_db(dbname)

    def set_container(self, cname):
        logging.info("DBService#set_container: {}".format(cname))
        self.cname = cname
        if self.graph_source == "cosmos_nosql":
            self.nosql_svc.set_container(cname)
        else :
            self.vcore_svc.set_coll(cname)

    async def close(self):
        logging.info("DBService#close()")
        if self.graph_source == "cosmos_nosql":
            await self.nosql_svc.close()
        else :
            await asyncio.sleep(0.01)
            self.vcore_svc.close()

