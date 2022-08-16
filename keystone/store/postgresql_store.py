import asyncio
import re
from datetime import datetime
import logging
import urllib.parse
import uuid
from typing import Dict, List

import aiopg
import psycopg2
from aiopg.sa import create_engine
from aiopg.sa.result import RowProxy
from scim2_filter_parser.queries import SQLQuery
from sqlalchemy import delete, insert, select, text, update, and_
from sqlalchemy.sql.base import ImmutableColumnCollection

from keystone.models.user import DEFAULT_USER_SCHEMA
from keystone.store import RDBMSStore
from keystone.store.pg_sql_queries import ddl_queries
from keystone.store import pg_models as tbl
from keystone.util.config import Config
from keystone.util.exc import ResourceNotFound

CONFIG = Config()
LOGGER = logging.getLogger(__name__)
CONN_REFRESH_INTERVAL_SEC = 1 * 60 * 60


def build_dsn(**kwargs):
    host = kwargs.get("host", CONFIG.get("store.pg_host"))
    port = kwargs.get("port", CONFIG.get("store.pg_port", 5432))
    username = kwargs.get("username", CONFIG.get("store.pg_username"))
    password = kwargs.get("password", CONFIG.get("store.pg_password"))
    database = kwargs.get("database", CONFIG.get("store.pg_database"))
    ssl_mode = kwargs.get("ssl_mode", CONFIG.get("store.pg_ssl_mode"))
    cred = username
    if password:
        cred = f"{cred}:{urllib.parse.quote(password)}"
    return f"postgres://{cred}@{host}:{port}/{database}?sslmode={ssl_mode}"


def set_up_schema(**kwargs):
    conn = psycopg2.connect(
        dsn=build_dsn(**kwargs)
    )
    schema = CONFIG.get("store.pg_schema", "public")
    cursor = conn.cursor()
    for q in ddl_queries:
        cursor.execute(q.format(schema))
    conn.commit()
    conn.close()


async def _transform_group(group_record: RowProxy) -> Dict:
    return {
        "id": group_record.id,
        "displayName": group_record.displayName,
        "members": [m for m in group_record.members if m.get("value")],
    }


async def _transform_user(user_record: RowProxy) -> Dict:
    return {
        "id": user_record.id,
        "userName": user_record.userName,
        "externalId": user_record.externalId,
        "schemas": user_record.schemas,
        "locale": user_record.locale,
        "name": user_record.name,
        "displayName": user_record.displayName,
        "active": user_record.active,
        "emails": user_record.emails,
        "groups": [g for g in user_record.groups if g.get("displayName")],
        **(user_record.customAttributes or {})
    }


class PostgresqlStore(RDBMSStore):
    engine: aiopg.sa.Engine = None
    schema: str
    entity_type: str
    nested_store_attr: str
    last_conn = None

    attr_map = {
        ("userName", None, None): "users.\"userName\"",
        ("displayName", None, None): "users.\"displayName\"",
        ("externalId", None, None): "users.\"externalId\"",
        ("id", None, None): "users.id",
        ("active", None, None): "users.active",
        ("locale", None, None): "users.locale",
        ("name", None, None): "users.name.formatted",
        ("emails", None, None): "user_emails.value",
        ("emails", "value", None): "user_emails.value",
        ("value", None, None): "users_groups.\"userId\"",
    }

    def __init__(self, entity_type: str, **conn_args):
        self.schema = CONFIG.get("store.pg_schema")
        self.entity_type = entity_type
        self.conn_args = conn_args

    async def get_engine(self):
        if not self.engine or not self.last_conn or (
                datetime.now() - self.last_conn).total_seconds() > CONN_REFRESH_INTERVAL_SEC:
            LOGGER.debug("Establishing new PostgreSQL connection")
            self.last_conn = datetime.now()
            self.engine = await create_engine(dsn=build_dsn(**self.conn_args))
            LOGGER.debug("Established new PostgreSQL connection")
        return self.engine

    async def term_connection(self):
        engine = await self.get_engine()
        if engine:
            engine.close()
            return await engine.wait_closed()

    async def _get_user_by_id(self, user_id: str) -> Dict:
        em_agg = text("""
            array_agg(json_build_object(
                'value', user_emails.value,
                'primary', user_emails.primary,
                'type', user_emails.type
            )) as emails
        """)
        gr_agg = text("""
            array_agg(json_build_object('displayName', groups."displayName")) as groups
        """)
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            q = select([tbl.users, em_agg, gr_agg]). \
                join(tbl.user_emails, tbl.users.c.id == tbl.user_emails.c.userId, isouter=True). \
                join(tbl.users_groups, tbl.users.c.id == tbl.users_groups.c.userId, isouter=True). \
                join(tbl.groups, tbl.groups.c.id == tbl.users_groups.c.groupId, isouter=True). \
                where(tbl.users.c.id == user_id). \
                group_by(text("1,2,3,4,5,6,7,8,9"))
            entity_record = None
            async for row in conn.execute(q):
                entity_record = row
                break
            if not entity_record:
                raise ResourceNotFound("User", user_id)

        return await _transform_user(entity_record)

    async def _get_group_by_id(self, group_id: str):
        mem_agg = text("""
            array_agg(json_build_object(
                'display', users."userName",
                'value', users."id"
            )) as members
        """)
        q = select([tbl.groups, mem_agg]). \
            join(tbl.users_groups, tbl.groups.c.id == tbl.users_groups.c.groupId, isouter=True). \
            join(tbl.users, tbl.users.c.id == tbl.users_groups.c.userId, isouter=True). \
            where(tbl.groups.c.id == group_id). \
            group_by(text("1,2,3"))
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            entity_record = None
            async for row in conn.execute(q):
                entity_record = row
                break
            if not entity_record:
                raise ResourceNotFound("Group", group_id)
        return await _transform_group(entity_record)

    async def get_by_id(self, resource_id: str):
        if self.entity_type == "users":
            return await self._get_user_by_id(resource_id)
        if self.entity_type == "groups":
            return await self._get_group_by_id(resource_id)

    async def search(self, _filter: str, start_index: int = 1, count: int = 100) -> tuple[list[Dict], int]:
        where = ""
        if _filter:
            parsed_q = SQLQuery(_filter, self.entity_type, self.attr_map)
            where = parsed_q.where_sql
            parsed_params = parsed_q.params_dict
            for k in parsed_params.keys():
                where = where.replace(f"{{{k}}}", f"'{parsed_params[k]}'")
        em_agg = text("""
            array_agg(json_build_object(
                'value', user_emails.value,
                'primary', user_emails.primary,
                'type', user_emails.type
            )) as emails
        """)
        gr_agg = text("""
            array_agg(json_build_object('displayName', groups."displayName")) as groups
        """)
        ct = text("count(*) OVER() as total")
        q = select([tbl.users, em_agg, gr_agg, ct]). \
            join(tbl.user_emails, tbl.users.c.id == tbl.user_emails.c.userId, isouter=True). \
            join(tbl.users_groups, tbl.users.c.id == tbl.users_groups.c.userId, isouter=True). \
            join(tbl.groups, tbl.groups.c.id == tbl.users_groups.c.groupId, isouter=True)
        if len(where) > 0:
            insensitive_like = re.compile(re.escape(" LIKE "), re.IGNORECASE)
            where = insensitive_like.sub(" ILIKE ", where)
            q = q.where(text(where))
        q = q.group_by(text("1,2,3,4,5,6,7,8,9")).offset(start_index - 1).fetch(count)
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            users = []
            total = 0
            async for row in conn.execute(q):
                users.append(await _transform_user(row))
                total = row.total

        return users, total

    async def update(self, resource_id: str, **kwargs: Dict):
        if self.entity_type == "users":
            return await self._update_user(resource_id, **kwargs)
        if self.entity_type == "groups":
            return await self._update_group(resource_id, **kwargs)

    async def _update_user(self, user_id: str, **kwargs: Dict) -> Dict:
        # "id" is immutable, and "groups" are updated through the groups API:
        immutable_cols = ["id", "groups"]
        for immutable_col in immutable_cols:
            if immutable_col in kwargs:
                del kwargs[immutable_col]
        update_emails = False
        emails = []
        if "emails" in kwargs:
            update_emails = True
            emails = kwargs["emails"]
            del kwargs["emails"]
        user_cols: ImmutableColumnCollection = tbl.users.c
        # Ensure non-existent columns didn't sneak into the update:
        clean_attributes = {
            attr: kwargs[attr] for attr in kwargs.keys()
            if attr in user_cols
        }
        q = update(tbl.users).where(tbl.users.c.id == user_id).values(**clean_attributes)
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            _ = await conn.execute(q)
        if update_emails:
            del_emails_q = delete(tbl.user_emails).where(tbl.users.c.id == user_id)
            ins_emails_q = insert(tbl.user_emails).values([
                {
                    "id": str(uuid.uuid4()),
                    "userId": user_id,
                    "primary": email.get("primary", True),
                    "value": email.get("value"),
                    "type": email.get("type")
                } for email in emails
            ])
            async with engine.acquire() as conn:
                _ = await conn.execute(del_emails_q)
                _ = await conn.execute(ins_emails_q)
        return await self._get_user_by_id(user_id)

    async def _update_group(self, group_id: str, **kwargs: Dict) -> Dict:
        if "id" in kwargs:
            del kwargs["id"]
        q = update(tbl.groups).where(tbl.groups.c.id == group_id).values(**kwargs)
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            _ = await conn.execute(q)
        return await self._get_group_by_id(group_id)

    async def create(self, resource: Dict):
        if self.entity_type == "users":
            return await self._create_user(resource)
        if self.entity_type == "groups":
            return await self._create_group(resource)

    async def _create_group(self, resource: Dict) -> Dict:
        group_id = resource.get("id") or str(uuid.uuid4())
        members = resource.get("members", [])
        insert_members = None
        if len(members) > 0:
            insert_members = insert(tbl.users_groups).values([
                {"userId": u.get("value"), "groupId": group_id} for u in members
            ])
        insert_group = insert(tbl.groups).values(
            id=group_id,
            schemas=resource.get("schemas"),
            displayName=resource.get("displayName")
        )
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            _ = await conn.execute(insert_group)
            if insert_members is not None:
                _ = await conn.execute(insert_members)

        return await self._get_group_by_id(group_id)

    async def _create_user(self, resource: Dict):
        custom_schemas = {
            schema: resource.get(schema, {})
            for schema in resource["schemas"] if schema != DEFAULT_USER_SCHEMA
        }
        user_id = resource.get("id") or str(uuid.uuid4())
        insert_user = insert(tbl.users).values(
            id=user_id,
            externalId=resource.get("externalId"),
            locale=resource.get("locale"),
            name=resource.get("name"),
            schemas=resource.get("schemas"),
            userName=resource.get("userName"),
            displayName=resource.get("displayName"),
            active=resource.get("active"),
            customAttributes=custom_schemas
        ).returning()
        insert_emails = insert(tbl.user_emails).values([
            {
                "id": str(uuid.uuid4()),
                "userId": user_id,
                "primary": email.get("primary", True),
                "value": email.get("value"),
                "type": email.get("type")
            } for email in resource.get("emails")
        ])
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            _ = await conn.execute(insert_user)
            _ = await conn.execute(insert_emails)
        return {**resource, "id": user_id}

    async def delete(self, resource_id: str):
        if self.entity_type == "users":
            return await self._delete_user(resource_id)
        if self.entity_type == "groups":
            return await self._delete_group(resource_id)

    async def _delete_user(self, user_id: str):
        del_q = [
            delete(tbl.user_emails).where(tbl.user_emails.c.userId == user_id),
            delete(tbl.users_groups).where(tbl.users_groups.c.userId == user_id),
            delete(tbl.users).where(tbl.users.c.id == user_id),
        ]
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            sel_q = select(tbl.users).where(tbl.users.c.id == user_id)
            user = None
            async for row in conn.execute(sel_q):
                user = row
                break
            if not user:
                raise ResourceNotFound("User", user_id)
            for q in del_q:
                _ = await conn.execute(q)
        return {}

    async def _delete_group(self, group_id: str):
        del_q = delete(tbl.groups).where(tbl.groups.c.id == group_id)
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            sel_q = select(tbl.groups).where(tbl.groups.c.id == group_id)
            group = None
            async for row in conn.execute(sel_q):
                group = row
                break
            if not group:
                raise ResourceNotFound("Group", group_id)
            _ = await conn.execute(del_q)
        return {}

    async def remove_users_from_group(self, user_ids: List[str], group_id: str):
        user_ids_s = ",".join([f"'{uid}'" for uid in user_ids])
        q = delete(tbl.users_groups).where(
            text(f"users_groups.\"groupId\" = '{group_id}' AND users_groups.\"userId\" IN ({user_ids_s})")
        )
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            _ = await conn.execute(q)
        return

    async def add_user_to_group(self, user_id: str, group_id: str):
        check_q = select(tbl.users_groups).where(
            and_(tbl.users_groups.c.userId == user_id, tbl.users_groups.c.groupId == group_id)
        )
        insert_q = insert(tbl.users_groups).values(userId=user_id, groupId=group_id)
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            async for row in await conn.execute(check_q):
                return
            _ = await conn.execute(insert_q)
        return

    async def set_group_members(self, user_ids: List[Dict], group_id: str):
        delete_q = delete(tbl.users_groups).where(tbl.users_groups.c.groupId == group_id)
        insert_q = insert(tbl.users_groups).values(
            [{"userId": uid, "groupId": group_id} for uid in user_ids]
        )
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            _ = await conn.execute(delete_q)
            _ = await conn.execute(insert_q)
        return

    async def search_members(self, _filter: str, group_id: str):
        parsed_q = SQLQuery(_filter, "users_groups", self.attr_map)
        where = parsed_q.where_sql
        parsed_params = parsed_q.params_dict
        for k in parsed_params.keys():
            where = where.replace(f"{{{k}}}", f"'{parsed_params[k]}'")
        q = select([tbl.users_groups]).join(tbl.users, tbl.users.c.id == tbl.users_groups.c.userId). \
            where(and_(tbl.users_groups.c.groupId == group_id, text(where)))
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            res = []
            async for row in await conn.execute(q):
                res.append({"value": row.userId})
        return res

    async def clean_up_store(self) -> None:
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            _ = await conn.execute(delete(tbl.users))
            _ = await conn.execute(delete(tbl.user_emails))
            _ = await conn.execute(delete(tbl.users_groups))
            _ = await conn.execute(delete(tbl.groups))
            if self.schema != "public":
                _ = await conn.execute(text(f"DROP SCHEMA IF EXISTS {self.schema} CASCADE"))
        return
