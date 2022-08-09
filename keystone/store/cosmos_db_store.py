import logging
import re
import uuid
from typing import Dict, Union

from azure.cosmos import CosmosClient, DatabaseProxy, exceptions, PartitionKey, ConsistencyLevel
from azure.cosmos.aio import (
    CosmosClient as AsyncCosmosClient,
    DatabaseProxy as AsyncDatabaseProxy
)
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.identity.aio import (
    ClientSecretCredential as AsyncClientSecretCredential,
    DefaultAzureCredential as AsyncDefaultAzureCredential
)
from scim2_filter_parser.queries import SQLQuery

from keystone.store import BaseStore
from keystone.util.config import Config
from keystone.util.exc import ResourceAlreadyExists

CONFIG = Config()
LOGGER = logging.getLogger(__name__)


async def get_client_credentials(async_client: bool = True):
    # TODO: SDK bug https://github.com/Azure/azure-sdk-for-python/issues/25405
    #       forces the usage of the main module to run aggregate queries with the
    #       'VALUE' keyword. The bug doesn't exist in the main module, therefore
    #       this function can currently produce non-async credentials.
    cosmos_account_key = CONFIG.get("store.cosmos_account_key")
    if cosmos_account_key:
        return cosmos_account_key
    tenant_id = CONFIG.get("store.tenant_id")
    client_id = CONFIG.get("store.client_id")
    client_secret = CONFIG.get("store.client_secret")
    if tenant_id and client_id and client_secret:
        aad_credentials = AsyncClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        ) if async_client else ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        return aad_credentials
    return AsyncDefaultAzureCredential() if async_client else DefaultAzureCredential()


async def remove_cosmos_metadata(resource: Dict):
    return {k: resource[k] for k in resource.keys() if not k.startswith("_")}


class CosmosDbStore(BaseStore):
    client: CosmosClient
    database: Union[DatabaseProxy, AsyncDatabaseProxy]
    key_attr: str

    attr_map = {
        ('userName', None, None): 'c.userName',
        ('displayName', None, None): 'c.displayName',
        ('externalId', None, None): 'c.externalId',
        ('id', None, None): 'c.id',
        ('active', None, None): 'c.active',
        ('meta', 'lastModified', None): 'c._ts',
        ('emails', None, None): 'c.emails.value',
        ('emails', 'value', None): 'c.emails.value',
    }

    def __init__(self, entity_name: str, key_attr: str = "id", unique_attribute: str = None):
        self.entity_name = entity_name
        self.key_attr = key_attr
        self.account_uri = CONFIG.get("store.cosmos_account_uri")
        self.unique_attribute = unique_attribute
        self.container_name = f"scim2{self.entity_name}"
        self.init_client()

    async def get_by_id(self, resource_id: str):
        client_creds = await get_client_credentials()
        uri = self.account_uri
        async with AsyncCosmosClient(uri, credential=client_creds) as client:
            database = client.get_database_client(CONFIG.get("store.cosmos_db_name"))
            container = database.get_container_client(self.container_name)
            resource = await container.read_item(item=resource_id, partition_key=resource_id)
        return await remove_cosmos_metadata(resource)

    async def _get_query_count(self, query: str, params: Dict):
        # TODO: SDK bug https://github.com/Azure/azure-sdk-for-python/issues/25405
        #       forces the usage of the main module to run aggregate queries with the
        #       'VALUE' keyword. The bug doesn't exist in the main module, therefore
        #       this function can currently uses the non-async client.
        client_creds = await get_client_credentials(async_client=False)
        try:
            c = CosmosClient(self.account_uri, credential=client_creds)
            db = c.get_database_client(CONFIG.get("store.cosmos_db_name"))
            co = db.get_container_client(self.container_name)
            count = 0
            for res in co.query_items(query=query, parameters=params, enable_cross_partition_query=True):
                count = res
                break
            return count
        except exceptions.CosmosHttpResponseError:
            raise

    async def search(self, _filter: str, start_index: int = 1, count: int = 100) -> tuple[list[Dict], int]:
        pagination = "OFFSET @offset LIMIT @limit"
        params = [
            {"name": "@offset", "value": start_index - 1},
            {"name": "@limit", "value": count},
        ]
        where = ""
        if _filter:
            # TODO: handle nested attributes properly
            parsed_q = SQLQuery(_filter, self.entity_name, self.attr_map)
            where = parsed_q.where_sql
            parsed_params = parsed_q.params_dict
            for k in parsed_params.keys():
                where = where.replace(f"{{{k}}}", f"@param{k}")
                params.append({"name": f"@param{k}", "value": parsed_params[k]})
        if len(where) > 0:
            replace_re = r"^(.*)(c.userName)\s+=\s+(@\w+)(.*)$"
            where = re.sub(replace_re, r"\1 STRINGEQUALS(\2, \3, true) \4", where)
            where = f"where {where}"

        query = f"SELECT * FROM c {where} {pagination}"
        client_creds = await get_client_credentials()
        uri = self.account_uri
        resources = []
        async with AsyncCosmosClient(uri, credential=client_creds) as client:
            try:
                database = client.get_database_client(CONFIG.get("store.cosmos_db_name"))
                container = database.get_container_client(self.container_name)
                iterator = container.query_items(query=query, parameters=params, populate_query_metrics=True)
                async for resource in iterator:
                    resources.append(await remove_cosmos_metadata(resource))
            except exceptions.CosmosHttpResponseError:
                raise
        count = await self._get_query_count(
            f"SELECT VALUE COUNT(c.id) FROM c {where}",
            params
        )
        return resources, count

    async def update(self, resource_id: str, **kwargs: Dict):
        client_creds = await get_client_credentials()
        uri = self.account_uri
        async with AsyncCosmosClient(uri, credential=client_creds) as client:
            database = client.get_database_client(CONFIG.get("store.cosmos_db_name"))
            container = database.get_container_client(self.container_name)
            try:
                resource = await remove_cosmos_metadata(
                    await container.read_item(item=resource_id, partition_key=resource_id)
                )
            except exceptions.CosmosResourceNotFoundError:
                raise
            resource.update(await self._sanitize(kwargs))
            await container.upsert_item(resource)
        return await remove_cosmos_metadata(resource)

    async def create(self, resource: Dict) -> Dict:
        client_creds = await get_client_credentials()
        uri = self.account_uri
        async with AsyncCosmosClient(uri, credential=client_creds) as client:
            database = client.get_database_client(CONFIG.get("store.cosmos_db_name"))
            container = database.get_container_client(self.container_name)
            resource_id = resource.get(self.key_attr) or str(uuid.uuid4())
            try:
                query = f"SELECT * FROM c " \
                        f"WHERE c.id = @id OR c.{self.unique_attribute} = @uniqueAttrValue"
                params = [
                    {"name": "@id", "value": resource_id},
                    {"name": "@uniqueAttrValue", "value": resource.get(self.unique_attribute)},
                ]
                found = False
                async for _ in container.query_items(query=query, parameters=params):
                    found = True
                    break
                if found:
                    raise ResourceAlreadyExists(self.entity_name.rstrip("s").title(), resource_id)
            except exceptions.CosmosResourceNotFoundError:
                pass
            resource[self.key_attr] = resource_id
            resource = await self._sanitize(resource)
            await container.upsert_item(resource)
        return await remove_cosmos_metadata(resource)

    async def delete(self, resource_id: str):
        client_creds = await get_client_credentials()
        uri = self.account_uri
        async with AsyncCosmosClient(uri, credential=client_creds) as client:
            database = client.get_database_client(CONFIG.get("store.cosmos_db_name"))
            container = database.get_container_client(self.container_name)
            try:
                _ = await container.delete_item(item=resource_id, partition_key=resource_id)
            except exceptions.CosmosResourceNotFoundError:
                pass
        return

    async def parse_filter_expression(self, expr: str):
        pass

    def init_client(self):
        account_uri = CONFIG.get("store.cosmos_account_uri")
        if not account_uri:
            raise ValueError(
                "Could not initialize Cosmos DB store. Missing configuration: 'store.cosmos_account_uri'"
            )
        tenant_id = CONFIG.get("store.tenant_id")
        client_id = CONFIG.get("store.client_id")
        client_secret = CONFIG.get("store.client_secret")
        cosmos_account_key = CONFIG.get("store.cosmos_account_key")
        if cosmos_account_key:
            client = CosmosClient(account_uri, credential=cosmos_account_key, consistency_level="Session")
        elif tenant_id and client_id and client_secret:
            aad_credentials = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            client = CosmosClient(account_uri, credential=aad_credentials, consistency_level="Session")
        else:
            client = CosmosClient(account_uri, credential=DefaultAzureCredential(), consistency_level="Session")
        cosmos_db_name = CONFIG.get("store.cosmos_db_name")
        try:
            database = client.create_database(cosmos_db_name)
        except (exceptions.CosmosResourceExistsError, exceptions.CosmosHttpResponseError):
            database = client.get_database_client(cosmos_db_name)

        try:
            unique_keys = None
            if self.unique_attribute:
                unique_keys = {
                    "uniqueKeys": [
                        {"paths": [f"/{self.unique_attribute}"]}
                    ]
                }
            _ = database.create_container(
                id=self.container_name,
                partition_key=PartitionKey(path=f"/{self.key_attr}"),
                unique_key_policy=unique_keys
            )
        except exceptions.CosmosResourceExistsError:
            _ = database.get_container_client(self.container_name)
        except exceptions.CosmosHttpResponseError:
            _ = database.get_container_client(self.container_name)
            pass

    async def clean_up_store(self):
        client_creds = await get_client_credentials()
        uri = self.account_uri
        async with AsyncCosmosClient(uri, credential=client_creds) as client:
            try:
                _ = await client.delete_database(CONFIG.get("store.cosmos_db_name"))
            except exceptions.CosmosHttpResponseError:
                raise
