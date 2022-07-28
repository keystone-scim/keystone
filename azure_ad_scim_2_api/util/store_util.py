import logging
from typing import Dict

from azure_ad_scim_2_api.store import BaseStore
from azure_ad_scim_2_api.store.memory_store import MemoryStore
from azure_ad_scim_2_api.store.cosmos_db_store import CosmosDbStore
from azure_ad_scim_2_api.util import ThreadSafeSingleton
from azure_ad_scim_2_api.util.config import Config


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
    if store_type == "CosmosDB":
        stores = Stores(
            users=CosmosDbStore("users", unique_attribute="userName"),
            groups=CosmosDbStore("groups", unique_attribute="displayName")
        )
    elif store_type == "InMemory":
        stores = Stores(
            users=MemoryStore("User"),
            groups=MemoryStore(
                "Group",
                name_uniqueness=True,
                resources=None,
                nested_store_attr="members"
            )
        )
    else:
        raise ValueError(f"Invalid store type: '{store_type}'")
    LOGGER.debug("Using '%s' store for users and groups", store_type)
    return stores
