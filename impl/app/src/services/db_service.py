import asyncio
import json
import logging

from src.services.ai_conversation import AiConversation
from src.services.base_db_service import BaseDBService
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


class DBService(BaseDBService):
    
    def __init__(self, override_graph_source=None):
        """ Constructor method; call initialize() immediately after this. """
        try:
            super().__init__(override_graph_source)
            # self.graph_source = ConfigService.graph_source()
            # if override_graph_source is not None:
            #     self.graph_source = override_graph_source  # used for testing & unit tests
            # self.vcore_svc  = None
            # self.nosql_svc = None
            # self.nosql_dbproxy = None
            # self.nosql_ctrproxy = None
            # self.dbname = None
            # self.graph_container = ConfigService.graph_container()
            # self.conversations_container = ConfigService.conversations_container()
            logging.info("DBService constructor complete; source: {}".format(self.graph_source))
        except Exception as e:
            logging.critical((str(e)))
            logging.exception(e, stack_info=True, exc_info=True)

    async def initialize(self):
        """ This method should be called immediately after the constructor. """
        if self.using_nosql():
            await self.initialize_cosmos_nosql()
        else :
            await self.initialize_cosmos_vcore()
        logging.info("DBService initialize() complete")

    async def save_conversation(self, conv: AiConversation|None) -> bool:
        """
        Example mongosh query:
        db.conversations.findOne({"conversation_id": "09d2aa6a-2f0e-4d8c-9a51-d393fd42c19b"})
        """
        if conv is not None:
            conv_id = conv.get_conversation_id()
            logging.info("DBService#save_conversation - {} {}".format(
                self.graph_source, conv_id)
            )
            if self.using_nosql():
                curr_container = self.nosql_svc.current_container()
                self.nosql_svc.set_container(self.dbname, self.conversations_container)
                doc = json.loads(conv.serialize())
                doc["_id"] = doc["uuid"]
                resp = await self.nosql_svc.upsert_item(doc)
                if curr_container is not None:
                    self.nosql_svc.set_container(curr_container)
            else:
                #await asyncio.sleep(0.01)
                self.vcore_svc.save_conversation(conv)

    async def load_conversation(self, conversation_id: str|None) -> AiConversation | None:
        """
        Example mongosh query:
        db.conversations.findOne({"conversation_id": "09d2aa6a-2f0e-4d8c-9a51-d393fd42c19b"})
        """
        logging.info("DBService#load_conversation - {}".format(conversation_id))
        if conversation_id == None:
            return AiConversation(None)  # return a new empty conversation
        
        if self.using_nosql():
            sql = "select from c where c.conversation_id = '{}' offset 0 limit 1".format(
                conversation_id)
            curr_container = self.nosql_svc
            self.nosql_svc.set_container(self.dbname, self.conversations_container)
            items = await self.nosql_svc.query_items(sql, True)
            if len(items) == 1:
                await self.nosql_svc.replace_item(conv)
            else:
                await self.nosql_svc.create_item(conv)
            if curr_container is not None:
                self.nosql_svc.set_container(curr_container)
        else:
            #await asyncio.sleep(0.01)
            self.vcore_svc.save_conversation(conv)

    async def close(self):
        logging.info("DBService#close()")
        if self.using_nosql():
            await self.nosql_svc.close()
        else :
            await asyncio.sleep(0.01)
            self.vcore_svc.close()
