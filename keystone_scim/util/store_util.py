import logging
from typing import Dict

from keystone_scim.store import BaseStore
from keystone_scim.store.memory_store import MemoryStore
from keystone_scim.store.cosmos_db_store import CosmosDbStore
from keystone_scim.store.mongodb_store import MongoDbStore
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
    store_type = CONFIG.get("store.type", "InMemory")
    store_impl: BaseStore
    if CONFIG.get("store.pg.host") is not None:
        user_store = PostgresqlStore("users")
        group_store = PostgresqlStore("groups")
        stores = Stores(
            users=user_store,
            groups=group_store
        )
    elif CONFIG.get("store.cosmos.account_uri"):
        stores = Stores(
            users=CosmosDbStore("users", unique_attribute="userName"),
            groups=CosmosDbStore("groups", unique_attribute="displayName")
        )
    elif CONFIG.get("store.mongo.host") or CONFIG.get("store.mongo.dsn"):
        stores = Stores(
            users=MongoDbStore("users"),
            groups=MongoDbStore("groups")
        )
    else:
        stores = Stores(
            users=MemoryStore("User"),
            groups=MemoryStore(
                "Group",
                name_uniqueness=True,
                resources=None,
                nested_store_attr="members"
            )
        )
    LOGGER.debug("Using '%s' store for users and groups", store_type)
    return stores
