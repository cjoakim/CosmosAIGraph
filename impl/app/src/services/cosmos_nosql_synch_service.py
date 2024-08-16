import datetime
import json
import logging
import time
import traceback
import uuid

from azure.cosmos import cosmos_client
from azure.cosmos import diagnostics
from azure.cosmos import exceptions

from src.services.config_service import ConfigService

# Instances of this class are used to access a Cosmos DB NoSQL
# account/database using the synchronous SDK methods.
# This module uses the 'azure-cosmos' SDK on PyPi.org, currently version 4.7.0.
# See https://pypi.org/project/azure-cosmos/
# See https://learn.microsoft.com/en-us/python/api/overview/azure/cosmos-readme?view=azure-python
# See https://azuresdkdocs.blob.core.windows.net/$web/python/azure-cosmos/4.7.0/azure.cosmos.html
# See https://github.com/Azure/azure-sdk-for-python/tree/azure-cosmos_4.7.0/sdk/cosmos/azure-cosmos/samples
# See https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search
# Chris Joakim, Microsoft


class CosmosNoSQLSynchService:

    def __init__(self, opts={}):
        self._dbname = None
        self._dbproxy = None
        self._ctrproxy = None
        self._cname = None
        self.reset_record_diagnostics()
        uri = ConfigService.cosmosdb_nosql_uri()
        key = ConfigService.cosmosdb_nosql_key1()
        if "enable_query_metrics" in opts.keys():
            self._query_metrics = True
        else:
            self._query_metrics = False
        self._client = cosmos_client.CosmosClient(uri, {"masterKey": key})

    def list_databases(self):
        """Return the list of database names in the account."""
        self.reset_record_diagnostics()
        return list(self._client.list_databases())

    def set_db(self, dbname):
        """Set the current database to the given dbname."""
        try:
            self.reset_record_diagnostics()
            self._dbname = dbname
            self._dbproxy = self._client.get_database_client(database=dbname)
        except Exception as e:
            logging.critical(str(e))
            print(traceback.format_exc())
        return self._dbproxy  # <class 'azure.cosmos.database.DatabaseProxy'>

    def list_containers(self):
        """Return the list of container names in the current database."""
        self.reset_record_diagnostics()
        return list(self._dbproxy.list_containers())

    def create_container(self, cname, partition_key, throughput):
        """Create a container in the current database."""
        try:
            self.reset_record_diagnostics()
            self._ctrproxy = self._dbproxy.create_container(
                id=cname,
                partition_key=partition_key.PartitionKey(path=partition_key),
                offer_throughput=throughput,
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics,
            )
            return self._ctrproxy
            # <class 'azure.cosmos.container.ContainerProxy'>
        except exceptions.CosmosResourceExistsError as excp:
            logging.critical(str(excp))
            print(traceback.format_exc())
            return self.set_container(cname)
        except Exception as excp2:
            logging.critical(str(excp2))
            print(traceback.format_exc())
            return None

    def set_container(self, cname):
        """Set the current container in the current database to the given cname."""
        self.reset_record_diagnostics()
        self._ctrproxy = self._dbproxy.get_container_client(cname)
        # <class 'azure.cosmos.container.ContainerProxy'>
        return self._ctrproxy

    def update_container_throughput(self, cname, throughput):
        """Update the throughput of the given container."""
        self.reset_record_diagnostics()
        self.set_container(cname)
        offer = self._ctrproxy.replace_throughput(
            throughput=int(throughput), response_hook=self._record_diagnostics
        )
        return offer

    def get_container_offer(self, cname):
        """Get the current offer (throughput) for the given container."""
        self.reset_record_diagnostics()
        self.set_container(cname)
        offer = self._ctrproxy.read_offer(response_hook=self._record_diagnostics)
        # <class 'azure.cosmos.offer.Offer'>
        return offer

    def delete_container(self, cname):
        """Delete the given container name in the current database."""
        try:
            self.reset_record_diagnostics()
            return self._dbproxy.delete_container(
                cname,
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics,
            )
        except Exception as excp:
            logging.critical(str(excp))
            print(traceback.format_exc())
            return None

    def upsert_doc(self, doc):
        """Upsert the given document in the current container."""
        try:
            self.reset_record_diagnostics()
            return self._ctrproxy.upsert_item(
                doc,
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics,
            )
        except Exception as excp:
            logging.critical(str(excp))
            print(traceback.format_exc())
            return None

    def delete_doc(self, doc, doc_pk):
        """Delete the given document in the current container."""
        try:
            self.reset_record_diagnostics()
            return self._ctrproxy.delete_item(
                doc,
                partition_key=doc_pk,
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics,
            )
        except Exception as excp:
            logging.critical(str(excp))
            print(traceback.format_exc())
            return None

    def read_doc(self, cname, doc_id, doc_pk):
        """Execute a point-read for container, document id, and partition key."""
        try:
            self.set_container(cname)
            self.reset_record_diagnostics()
            return self._ctrproxy.read_item(
                doc_id,
                partition_key=doc_pk,
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics,
            )
        except Exception as excp:
            logging.critical(str(excp))
            print(traceback.format_exc())
            return None

    def query_container(self, cname, sql, xpartition, max_count):
        """Execute a given SQL query of the given container name."""
        try:
            self.set_container(cname)
            self.reset_record_diagnostics()
            return self._ctrproxy.query_items(
                query=sql,
                enable_cross_partition_query=xpartition,
                max_item_count=max_count,
                populate_query_metrics=self._query_metrics,
                response_hook=self._record_diagnostics,
            )
        except Exception as excp:
            logging.critical(str(excp))
            print(traceback.format_exc())
            return excp

    def close(self) -> None:
        """ close the client if it exists """
        if (self._client != None):
            self._client.close()
            logging.info("CosmosNoSQLService - client closed")

    # Metrics and Diagnostics

    def enable_query_metrics(self):
        """Return a boolean indicating whether query metrics are enabled."""
        self._query_metrics = True

    def disable_query_metrics(self):
        """Set query metrics to False."""
        self._query_metrics = False

    def reset_record_diagnostics(self):
        """Reset the record diagnostics in this object."""
        self._record_diagnostics = diagnostics.RecordDiagnostics()

    def print_record_diagnostics(self):
        """Print the record diagnostics."""
        print(f"record_diagnostics: {self._record_diagnostics.headers}")
        print(str(type(self._record_diagnostics.headers)))
        keys = self._record_diagnostics.headers.keys()
        print(str(type(keys)))
        print(keys)
        for header in self._record_diagnostics.headers.items():
            print(header)
            print(str(type(header)))

    def record_diagnostics_headers_dict(self):
        """Read and return the record diagnostics headers as a dictionary."""
        data = {}
        for header in self._record_diagnostics.headers.items():
            key, val = header  # unpack the header 2-tuple
            data[key] = val
        return data

    def print_last_request_charge(self):
        """Print the last request charge and activity id."""
        charge = self.last_request_charge()
        activity = self.last_activity_id()
        print(f"last_request_charge: {charge} activity: {activity}")

    def last_request_charge(self):
        """Return the last request charge in RUs, default to -1."""
        header = "x-ms-request-charge"
        if header in self._record_diagnostics.headers:
            return self._record_diagnostics.headers[header]
        return -1

    def last_activity_id(self):
        """Return the last diagnostics activity id, default to None."""
        header = "x-ms-activity-id"
        if header in self._record_diagnostics.headers:
            return self._record_diagnostics.headers[header]
        return None
