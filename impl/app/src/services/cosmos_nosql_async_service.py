import datetime
import json
import logging
import time
import traceback
import uuid

import asyncio
from azure.cosmos import exceptions, PartitionKey
from azure.cosmos.aio import CosmosClient

from src.services.config_service import ConfigService

# Instances of this class are used to access a Cosmos DB NoSQL
# account/database using the asynchronous SDK methods.
# This module uses the 'azure-cosmos' SDK on PyPi.org, currently version 4.7.0.
# See https://pypi.org/project/azure-cosmos/
# See https://learn.microsoft.com/en-us/python/api/overview/azure/cosmos-readme?view=azure-python
# See https://azuresdkdocs.blob.core.windows.net/$web/python/azure-cosmos/4.7.0/azure.cosmos.html
# See https://github.com/Azure/azure-sdk-for-python/tree/azure-cosmos_4.7.0/sdk/cosmos/azure-cosmos/samples
# See https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search
# Chris Joakim, Microsoft
# cj, 8/14 - this class is WIP - synch methods being transitioned to async


# azure_logger can be used to set the verbosity of the Azure and Cosmos SDK logging
azure_logger = logging.getLogger('azure')
azure_logger.setLevel(logging.WARNING)


class CosmosNoSQLAsyncService:

    def __init__(self, opts={}):
        # https://www.slingacademy.com/article/python-defining-a-class-with-an-async-constructor/
        # https://stackoverflow.com/questions/33128325/how-to-set-class-attribute-with-await-in-init
        self._dbname = None
        self._dbproxy = None
        self._ctrproxy = None
        self._cname = None
        #self.reset_record_diagnostics()
        self.uri = ConfigService.cosmosdb_nosql_uri()
        self.key = ConfigService.cosmosdb_nosql_key1()
        self._client = None
        logging.info("CosmosNoSQLAsyncService - __init__ completed")

    async def initialize(self):
        """ This method should be called after the above constructor. """
        self._client = CosmosClient(self.uri, self.key)
        await self._client.__aenter__()  # this piece is important for the SDK to cache account information
        logging.info("CosmosNoSQLAsyncService - initialize() completed")

    async def close(self):
        if self._client is not None:
            await self._client.close()
            logging.info("CosmosNoSQLAsyncService - client closed")

    async def list_databases(self):
        """Return the list of database names in the account."""
        #return list(await self._client.list_databases())
        dblist = list()
        async for db in self._client.list_databases():
            dblist.append(db["id"])
        return dblist
    
    def set_db(self, dbname):
        """Set the current database to the given dbname."""
        try:
            self._dbname = dbname
            self._dbproxy = self._client.get_database_client(dbname)
        except Exception as e:
            logging.critical(str(e))
            print(traceback.format_exc())
        return self._dbproxy  # <class 'azure.cosmos.aio._database.DatabaseProxy'>

    def set_container(self, cname):
        """Set the current container in the current database to the given cname."""
        self._ctrproxy = self._dbproxy.get_container_client(cname)
        return self._ctrproxy  # <class 'azure.cosmos.aio._container.ContainerProxy'>

    async def list_containers(self):
        """Return the list of container names in the current database."""
        container_list = list()
        async for container in self._dbproxy.list_containers():
            container_list.append(container["id"])
        return container_list

    async def point_read(self, id, pk):
        return await self._ctrproxy.read_item(item=id, partition_key=pk)
        
    async def upsert_item(self, doc):
        return await self._ctrproxy.upsert_item(body=doc)
        
    async def delete_item(self, id, pk):
        return await self._ctrproxy.delete_item(item=id, partition_key=pk)
        
    # https://github.com/Azure/azure-sdk-for-python/blob/azure-cosmos_4.7.0/sdk/cosmos/azure-cosmos/samples/document_management_async.py

    

    # def upsert_doc(self, doc):
    #     """Upsert the given document in the current container."""
    #     try:
    #         self.reset_record_diagnostics()
    #         return self._ctrproxy.upsert_item(
    #             doc,
    #             populate_query_metrics=self._query_metrics,
    #             response_hook=self._record_diagnostics,
    #         )
    #     except Exception as excp:
    #         logging.critical(str(excp))
    #         print(traceback.format_exc())
    #         return None

    # def delete_doc(self, doc, doc_pk):
    #     """Delete the given document in the current container."""
    #     try:
    #         self.reset_record_diagnostics()
    #         return self._ctrproxy.delete_item(
    #             doc,
    #             partition_key=doc_pk,
    #             populate_query_metrics=self._query_metrics,
    #             response_hook=self._record_diagnostics,
    #         )
    #     except Exception as excp:
    #         logging.critical(str(excp))
    #         print(traceback.format_exc())
    #         return None

    # def read_doc(self, cname, doc_id, doc_pk):
    #     """Execute a point-read for container, document id, and partition key."""
    #     try:
    #         self.set_container(cname)
    #         self.reset_record_diagnostics()
    #         return self._ctrproxy.read_item(
    #             doc_id,
    #             partition_key=doc_pk,
    #             populate_query_metrics=self._query_metrics,
    #             response_hook=self._record_diagnostics,
    #         )
    #     except Exception as excp:
    #         logging.critical(str(excp))
    #         print(traceback.format_exc())
    #         return None

    # def query_container(self, cname, sql, xpartition, max_count):
    #     """Execute a given SQL query of the given container name."""
    #     try:
    #         self.set_container(cname)
    #         self.reset_record_diagnostics()
    #         return self._ctrproxy.query_items(
    #             query=sql,
    #             enable_cross_partition_query=xpartition,
    #             max_item_count=max_count,
    #             populate_query_metrics=self._query_metrics,
    #             response_hook=self._record_diagnostics,
    #         )
    #     except Exception as excp:
    #         logging.critical(str(excp))
    #         print(traceback.format_exc())
    #         return excp

    # def close(self) -> None:
    #     """ close the client if it exists """
    #     if (self._client != None):
    #         self._client.close()
    #         logging.info("CosmosNoSQLService - client closed")

    # # Metrics and Diagnostics

    # def enable_query_metrics(self):
    #     """Return a boolean indicating whether query metrics are enabled."""
    #     self._query_metrics = True

    # def disable_query_metrics(self):
    #     """Set query metrics to False."""
    #     self._query_metrics = False

    # def reset_record_diagnostics(self):
    #     """Reset the record diagnostics in this object."""
    #     self._record_diagnostics = diagnostics.RecordDiagnostics()

    # def print_record_diagnostics(self):
    #     """Print the record diagnostics."""
    #     print(f"record_diagnostics: {self._record_diagnostics.headers}")
    #     print(str(type(self._record_diagnostics.headers)))
    #     keys = self._record_diagnostics.headers.keys()
    #     print(str(type(keys)))
    #     print(keys)
    #     for header in self._record_diagnostics.headers.items():
    #         print(header)
    #         print(str(type(header)))

    # def record_diagnostics_headers_dict(self):
    #     """Read and return the record diagnostics headers as a dictionary."""
    #     data = {}
    #     for header in self._record_diagnostics.headers.items():
    #         key, val = header  # unpack the header 2-tuple
    #         data[key] = val
    #     return data

    # def print_last_request_charge(self):
    #     """Print the last request charge and activity id."""
    #     charge = self.last_request_charge()
    #     activity = self.last_activity_id()
    #     print(f"last_request_charge: {charge} activity: {activity}")

    # def last_request_charge(self):
    #     """Return the last request charge in RUs, default to -1."""
    #     header = "x-ms-request-charge"
    #     if header in self._record_diagnostics.headers:
    #         return self._record_diagnostics.headers[header]
    #     return -1

    # def last_activity_id(self):
    #     """Return the last diagnostics activity id, default to None."""
    #     header = "x-ms-activity-id"
    #     if header in self._record_diagnostics.headers:
    #         return self._record_diagnostics.headers[header]
    #     return None
