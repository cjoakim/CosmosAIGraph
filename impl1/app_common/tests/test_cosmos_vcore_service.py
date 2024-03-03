import os
import time
import pytest

from pysrc.services.cosmos_vcore_service import CosmosVCoreService
from pysrc.services.config_service import ConfigService
from pysrc.util.fs import FS

# an actual Cosmos DB Mongo vCore account is used in these tests


def test_conn_str_config():
    ConfigService.set_standard_unit_test_env_vars()
    conn_str = ConfigService.mongo_vcore_conn_str()
    assert conn_str.startswith("mongodb+srv://")
    assert ".mongocluster.cosmos.azure.com" in conn_str


def test_meta_and_crud_operations():
    ConfigService.set_standard_unit_test_env_vars()
    opts = dict()
    opts["conn_string"] = ConfigService.mongo_vcore_conn_str()
    vcore = CosmosVCoreService(opts)
    assert "pymongo.mongo_client.MongoClient" in str(type(vcore.get_client()))

    epoch = int(time.time())
    new_dbname = "tempdb_{}".format(epoch)
    new_collname = "tempcoll_{}".format(epoch)

    try:
        # test initial state:
        # the 'unittests' collection in 'dev' database is assumed to exist.
        dbs = vcore.list_databases()
        assert "dev" in dbs
        vcore.set_db("dev")
        vcore.set_coll("unittests")
        colls = vcore.list_collections()
        assert "unittests" in colls

        # create a temporary database with a temporary collection
        vcore.set_db(new_dbname)
        vcore.set_coll(new_collname)

        # create a document in the temporary collection, read it back and verify
        doc = dict()
        doc["name"] = "testvalue"
        vcore.insert_doc(doc)
        assert vcore.count_docs({}) == 1
        cursor, docs = vcore.find({}), list()
        for doc in cursor:
            docs.append(doc)
        assert len(docs) == 1
        assert docs[0]["name"] == "testvalue"

        # index retrieval and creation
        indexes = vcore.get_coll_indexes(new_collname)
        assert indexes == {"_id_": {"key": [("_id", 1)], "v": 2}}
        vcore.create_simple_index("name")
        indexes = vcore.get_coll_indexes(new_collname)
        assert indexes == {
            "_id_": {"v": 2, "key": [("_id", 1)]},
            "name_1": {"v": 2, "key": [("name", 1)]},
        }

        # veriify that the new database and collection exist
        assert new_dbname in vcore.list_databases()
        assert new_collname in vcore.list_collections()

        # verify that document deletion works
        vcore.delete_many({})
        assert vcore.count_docs({}) == 0

        db_stats = vcore.command_db_stats()
        FS.write_json(db_stats, "tmp/test_cosmos_vcore_service_db_stats.json")
        assert type(db_stats) == dict

        coll_stats = vcore.command_coll_stats(new_collname)
        FS.write_json(coll_stats, "tmp/test_cosmos_vcore_service_coll_stats.json")
        assert type(coll_stats) == dict

        commands = vcore.command_list_commands()
        FS.write_json(commands, "tmp/test_cosmos_vcore_service_commands.json")
        assert type(commands) == dict

        shard_info = vcore.get_shard_info()
        FS.write_json(shard_info, "tmp/test_cosmos_vcore_shard_info.json")
        assert type(shard_info) == dict

        indexes = vcore.get_coll_indexes(new_collname)
        if indexes is not None:
            FS.write_json(indexes, "tmp/test_cosmos_vcore_indexes.json")
            assert type(indexes) == dict

        # cleanup - delete the temporary container and db
        # we want the test to fail if these operations do not succeed
        vcore.delete_container(new_collname)
        assert new_collname not in vcore.list_collections()
        vcore.delete_database(new_dbname)
        assert new_dbname not in vcore.list_databases()
    except Exception as excp:
        print(str(excp))
        vcore.delete_database(new_dbname)
        assert False

    try:
        # cleanup any previous remnant tempdb_ databases with no test assertions
        remnant_dblist = vcore.list_databases()
        FS.write_json(remnant_dblist, "tmp/test_cosmos_vcore_remnant_dblist.json")
        for dbname in remnant_dblist:
            if dbname.startswith("tempdb_"):
                vcore.delete_database(dbname)
    except Exception as excp:
        pass


@pytest.mark.skip(reason="TODO - implement")
def test_build_with_cosmos_documents():
    ConfigService.set_standard_unit_test_env_vars()
    assert 1 == 1
