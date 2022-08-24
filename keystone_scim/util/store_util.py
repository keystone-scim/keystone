import logging
from typing import Dict

from keystone_scim.store import BaseStore
from keystone_scim.store.memory_store import MemoryStore
from keystone_scim.store.cosmos_db_store import CosmosDbStore
from keystone_scim.store.mongodb_store import MongoDbStore
from keystone_scim.store.mysql_store import MySqlStore
from keystone_scim.store.postgresql_store import PostgresqlStore
from keystone_scim.util import ThreadSafeSingleton
from keystone_scim.util.config import Config


CONFIG = Config()
LOGGER = logging.getLogger(__name__)


class Stores(metaclass=ThreadSafeSingleton):
    impl: Dict[str, BaseStore] = {}

    def __init__(self, **impl):
        for k in impl.keys():
            self.impl[k] = impl[k]

    def get(self, store_name: str):
        return self.impl.get(store_name)


def init_stores():
    store_impl: BaseStore
    if CONFIG.get("store.pg.host") is not None:
        store_type = "PostgreSQL"
        user_store = PostgresqlStore("users")
        group_store = PostgresqlStore("groups")
        stores = Stores(
            users=user_store,
            groups=group_store
        )
    elif CONFIG.get("store.mysql.host") is not None:
        store_type = "MySQL"
        user_store = MySqlStore("users")
        group_store = MySqlStore("groups")
        stores = Stores(
            users=user_store,
            groups=group_store
        )
    elif CONFIG.get("store.cosmos.account_uri"):
        store_type = "Cosmos DB"
        stores = Stores(
            users=CosmosDbStore("users", unique_attribute="userName"),
            groups=CosmosDbStore("groups", unique_attribute="displayName")
        )
    elif CONFIG.get("store.mongo.host") or CONFIG.get("store.mongo.dsn"):
        store_type = "MongoDB"
        stores = Stores(
            users=MongoDbStore("users"),
            groups=MongoDbStore("groups")
        )
    else:
        store_type = "In-Memory"
        stores = Stores(
            users=MemoryStore("User"),
            groups=MemoryStore(
                "Group",
                name_uniqueness=True,
                resources=None,
                nested_store_attr="members"
            )
        )
    LOGGER.info("Using the %s data store", store_type)
    return stores
