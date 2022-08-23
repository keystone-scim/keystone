import asyncio
import urllib.parse
from typing import Dict, List

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collation import Collation
from scim2_filter_parser import ast
from scim2_filter_parser.ast import LogExpr, Filter, AttrExpr, CompValue, AttrPath, AST
from scim2_filter_parser.lexer import SCIMLexer
from scim2_filter_parser.parser import SCIMParser

from keystone_scim.store import DocumentStore
from keystone_scim.util.config import Config
from keystone_scim.util.exc import ResourceNotFound

CONFIG = Config()


def build_dsn(**kwargs):
    dsn = kwargs.get("dsn", CONFIG.get("store.mongo.dsn"))
    if dsn:
        return dsn
    host = kwargs.get("host", CONFIG.get("store.mongo.host"))
    port = kwargs.get("port", CONFIG.get("store.mongo.port", 5432))
    username = kwargs.get("username", CONFIG.get("store.mongo.username"))
    password = kwargs.get("password", CONFIG.get("store.mongo.password"))
    tls = kwargs.get("tls", CONFIG.get("store.mongo.tls", "true"))
    if type(tls) == bool:
        tls = "true" if tls is True else "false"
    replica_set = kwargs.get("replica_set", CONFIG.get("store.mongo.replica_set"))
    cred = username
    if password:
        cred = f"{cred}:{urllib.parse.quote(password)}"
    query_params = {}
    if tls:
        query_params["tls"] = tls
    if replica_set:
        query_params["replicaSet"] = replica_set
    return f"mongodb://{cred}@{host}:{port}/?tls={tls}"


async def set_up(**kwargs):
    client = AsyncIOMotorClient(build_dsn(**kwargs))
    db_name = kwargs.get("database", CONFIG.get("store.mongo.database"))
    users_collection = client[db_name]["users"]
    groups_collection = client[db_name]["groups"]
    _ = await users_collection.create_index([("userName", 1)], unique=True,
                                            collation=Collation(locale="en", strength=2))
    _ = await users_collection.create_index([("emails.value", 1)], collation=Collation(locale="en", strength=2))
    _ = await groups_collection.create_index([("displayName", 1)], unique=True,
                                             collation=Collation(locale="en", strength=2))


async def _transform_user(item: Dict) -> Dict:
    item_id: ObjectId = item.get("_id")
    user = {**item}
    if item_id:
        user["id"] = str(item_id)
        del user["_id"]
    return user


async def _transform_group(item: Dict) -> Dict:
    return {
        "id": str(item.get("_id")),
        "schemas": item.get("schemas"),
        "displayName": item.get("displayName"),
        "meta": item.get("meta"),
        "members": [{"value": str(m.get("_id")), "display": m.get("userName")} for m in item.get("userMembers", [])]
    }


class MongoDbStore(DocumentStore):
    client: AsyncIOMotorClient
    entity_type: str

    def __init__(self, entity_type: str, **conn_args):
        self.entity_type = entity_type
        self.client = AsyncIOMotorClient(build_dsn(**conn_args))
        self.db_name = conn_args.get("database", CONFIG.get("store.mongo.database"))

    async def _get_group_by_id(self, group_id: ObjectId) -> Dict:
        aggregate = [
            {
                "$match": {"_id": group_id},
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "members",
                    "foreignField": "_id",
                    "as": "userMembers",
                }
            }
        ]
        async for group in self.collection.aggregate(aggregate, collation={"locale": "en", "strength": 2}):
            return await _transform_group(group)

        raise ResourceNotFound("group", str(group_id))

    async def _get_user_by_id(self, user_id: ObjectId) -> Dict:
        resource = await self.collection.find_one({"_id": user_id})
        if resource:
            return await _transform_user(
                await self._sanitize(resource)
            )
        raise ResourceNotFound("User", str(user_id))

    async def get_by_id(self, resource_id: str) -> Dict:
        _resource_id = ObjectId(resource_id)
        if self.entity_type == "users":
            return await self._get_user_by_id(_resource_id)
        return await self._get_group_by_id(_resource_id)

    async def search(self, _filter: str = None, start_index: int = 1, count: int = 100) -> tuple[list[Dict], int]:
        parsed_filter = {}
        if _filter:
            token_stream = SCIMLexer().tokenize(_filter)
            ast_nodes = SCIMParser().parse(token_stream)
            # We only need the root node, which contains all the references in the tree for traversal:
            _, root = ast.flatten(ast_nodes)[0]
            parsed_filter = await self.parse_scim_filter(root)
        aggregate = [
            {"$facet": {
                "data": [
                    {"$match": parsed_filter},
                    {"$skip": start_index - 1},
                    {"$limit": count},
                ],
                "totalCount": [
                    {"$match": parsed_filter},
                    {"$count": "count"},
                ]
            }}
        ]
        res = []
        total = 0
        async for resource in self.collection.aggregate(aggregate, collation={"locale": "en", "strength": 2}):
            res = [await _transform_user(r) for r in resource.get("data")]
            total = resource.get("totalCount")[0]["count"] if len(resource.get("totalCount")) > 0 else 0
            break

        return res, total

    async def update(self, resource_id: str, **kwargs: Dict):
        resource = await self.collection.find_one({"_id": ObjectId(resource_id)})
        if not resource:
            ResourceNotFound("User", resource_id)
        _ = await self.collection.replace_one({"_id": ObjectId(resource_id)}, kwargs, True)
        return await self.get_by_id(resource_id)

    async def create(self, resource: Dict):
        sanitized = await self._sanitize(resource)
        if "id" in sanitized:
            del sanitized["id"]
        return await self._create_user(sanitized) if self.entity_type == "users" else await self._create_group(
            sanitized)

    @property
    def collection(self):
        return self.client[self.db_name][self.entity_type]

    async def _create_user(self, user: Dict):
        inserted_id = (await self.collection.insert_one(user)).inserted_id
        inserted_user = await self.collection.find_one(inserted_id)
        return await _transform_user(inserted_user)

    async def _create_group(self, group: Dict):
        group["members"] = [ObjectId(m.get("value")) for m in group.get("members", [])]
        inserted_id = (await self.collection.insert_one(group)).inserted_id
        inserted_group = await self.collection.find_one(inserted_id)
        return await _transform_group(inserted_group)

    async def delete(self, resource_id: str):
        resource = await self.collection.find_one({"_id": ObjectId(resource_id)})
        if not resource:
            raise ResourceNotFound(self.entity_type, resource_id)
        _ = await self.collection.delete_one({"_id": ObjectId(resource_id)})
        return {}

    async def clean_up_store(self):
        return await self.collection.drop()

    async def parse_scim_filter(self, node: AST, namespace: str = None) -> Dict:
        if isinstance(node, Filter):
            ns = node.namespace.attr_name if node.namespace else None
            expr = await self.parse_scim_filter(node.expr, ns or namespace)
            return {"$not": expr} if node.negated else expr
        if isinstance(node, AttrExpr):
            # Parse an atomic comparison operation:
            operator = node.value.lower()
            attr_path: AttrPath = node.attr_path
            attr = attr_path.attr_name
            if attr_path.sub_attr:
                sub_attr = attr_path.sub_attr.value
                attr = f"{attr}.{sub_attr}"
            comp_value: CompValue = node.comp_value
            value = comp_value.value if comp_value else None
            if value:
                if operator.lower() == "eq" and attr == "id":
                    return {
                        "_id": ObjectId(value)
                    }
                if operator.lower() == "co" and attr.endswith("emails"):
                    return {
                        "emails.value": value
                    }
                if operator.lower() == "sw":
                    operator = "regex"
                    value = f"^{value}"
                elif operator.lower() == "ew":
                    operator = "regex"
                    value = f"{value}$"
                elif operator.lower() == "co":
                    operator = "regex"
                    value = f"{value}"
            if namespace:
                attr = f"{namespace}.{attr}"
            return {
                attr: {f"${operator}": value}
            }
        if isinstance(node, LogExpr):
            # Parse a logical expression:
            operator = node.op.lower()
            l_exp = await self.parse_scim_filter(node.expr1, namespace)
            r_exp = await self.parse_scim_filter(node.expr2, namespace)
            return {
                f"${operator}": [
                    l_exp,
                    r_exp,
                ]
            }

    async def _update_group(self, group_id: str, **kwargs) -> Dict:
        group = await self.collection.find_one({"_id": ObjectId(group_id)})
        if not group:
            raise ResourceNotFound("group", group_id)
        _ = await self.collection.replace_one(
            {"_id": ObjectId(group_id)},
            kwargs,
            True
        )
        return await _transform_group(await self.collection.find_one({"_id": ObjectId(group_id)}))

    async def remove_users_from_group(self, user_ids: List[str], group_id: str):
        group = await self.collection.find_one({"_id": ObjectId(group_id)})
        if not group:
            raise ResourceNotFound("group", group_id)
        _ = await self.collection.update_one(
            {"_id": ObjectId(group_id)},
            {"$pull": {"members": {"$in": [ObjectId(user_id) for user_id in user_ids]}}},
        )

    async def add_user_to_group(self, user_id: str, group_id: str):
        group = await self.collection.find_one({"_id": ObjectId(group_id)})
        if not group:
            raise ResourceNotFound("group", group_id)
        members = {str(g): None for g in group.get("members", [])}
        if True or user_id not in members:
            _ = await self.collection.update_one({"_id": ObjectId(group_id)},
                                                 {"$push": {"members": ObjectId(user_id)}})

    async def set_group_members(self, user_ids: List[str], group_id: str):
        group = await self.collection.find_one({"_id": ObjectId(group_id)})
        if not group:
            raise ResourceNotFound("group", group_id)
        _ = await self.collection.replace_one(
            {"_id": ObjectId(group_id)},
            {"members": [ObjectId(user_id) for user_id in user_ids]},
            True
        )
