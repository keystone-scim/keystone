import logging
import urllib.parse
import uuid
from typing import Dict

import aiopg
from aiopg.sa import create_engine
from scim2_filter_parser.queries import SQLQuery
from sqlalchemy import delete, insert, select, text

from keystone.models.user import DEFAULT_USER_SCHEMA
from keystone.store import BaseStore
from keystone.store.pg_sql_queries import ddl_queries
from keystone.store import pg_models as models
from keystone.util.config import Config
from keystone.util.exc import ResourceNotFound

CONFIG = Config()
LOGGER = logging.getLogger(__name__)


class PostgresqlStore(BaseStore):
    engine: aiopg.sa.Engine
    schema: str
    entity_type: str

    attr_map = {
        ('userName', None, None): 'users."userName"',
        ('displayName', None, None): 'users."displayName"',
        ('externalId', None, None): 'users."externalId"',
        ('id', None, None): 'users.id',
        ('active', None, None): 'users.active',
        ('emails', None, None): 'c.emails.value',
        ('emails', 'value', None): 'c.emails.value',
    }

    def __init__(self, entity_type: str):
        self.schema = CONFIG.get("store.pg_schema")
        self.entity_type = entity_type

    async def setup(self):
        dsn = await self.build_dsn()
        self.engine = await create_engine(dsn=dsn)
        async with self.engine.acquire() as conn:
            for q in ddl_queries:
                _ = await conn.execute(q.format(self.schema))
        return

    async def build_dsn(self):
        host = CONFIG.get("store.pg_host")
        port = CONFIG.get("store.pg_port", 5432)
        username = CONFIG.get("store.pg_username")
        password = CONFIG.get("store.pg_password")
        database = CONFIG.get("store.pg_database")
        ssl_mode = CONFIG.get("store.pg_ssl_mode")
        cred = username
        if password:
            cred = f"{cred}:{urllib.parse.quote(password)}"
        return f"postgres://{cred}@{host}:{port}/{database}?sslmode={ssl_mode}"

    async def _transform_user(self, user_record) -> Dict:
        user_dict = {
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

        return user_dict

    async def _transform_group(self):
        pass

    async def _get_user_by_id(self, user_id: str):
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
        async with self.engine.acquire() as conn:
            q = select([models.users, em_agg, gr_agg]). \
                join(models.user_emails, models.users.c.id == models.user_emails.c.userId, isouter=True). \
                join(models.users_groups, models.users.c.id == models.users_groups.c.userId, isouter=True). \
                join(models.groups, models.groups.c.id == models.users_groups.c.groupId, isouter=True). \
                where(models.users.c.id == user_id). \
                group_by(text("1,2,3,4,5,6,7,8,9"))
            entity_record = None
            async for row in conn.execute(q):
                entity_record = row
                break
            if not entity_record:
                raise ResourceNotFound("User", user_id)

        return await self._transform_user(entity_record)

    async def _get_group_by_id(self, group_id: str):
        pass

    async def get_by_id(self, resource_id: str):
        if self.entity_type == "users":
            return await self._get_user_by_id(resource_id)
        if self.entity_type == "groups":
            return await self._get_group_by_id(resource_id)
        return

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
        q = select([models.users, em_agg, gr_agg, ct]). \
            join(models.user_emails, models.users.c.id == models.user_emails.c.userId, isouter=True). \
            join(models.users_groups, models.users.c.id == models.users_groups.c.userId, isouter=True). \
            join(models.groups, models.groups.c.id == models.users_groups.c.groupId, isouter=True). \
            where(text(where)).group_by(text("1,2,3,4,5,6,7,8,9")).offset(start_index - 1).fetch(count)
        async with self.engine.acquire() as conn:
            users = []
            total = 0
            async for row in conn.execute(q):
                users.append(await self._transform_user(row))
                total = row.total

        return users, total

    async def update(self, resource_id: str, **kwargs: Dict):
        pass

    async def create(self, resource: Dict):
        if self.entity_type == "users":
            return await self._create_user(resource)
        if self.entity_type == "groups":
            pass
        return

    async def _create_user(self, resource: Dict):
        custom_schemas = {
            schema: resource.get(schema, {})
            for schema in resource["schemas"] if schema != DEFAULT_USER_SCHEMA
        }
        user_id = resource.get("id") or str(uuid.uuid4())
        insert_user = insert(models.users).values(
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
        insert_emails = insert(models.user_emails).values([
            {
                "id": str(uuid.uuid4()),
                "userId": user_id,
                "primary": email.get("primary", True),
                "value": email.get("value"),
                "type": email.get("type")
            } for email in resource.get("emails")
        ])
        async with self.engine.acquire() as conn:
            _ = await conn.execute(insert_user)
            _ = await conn.execute(insert_emails)
        return {**resource, "id": user_id}

    async def delete(self, resource_id: str):
        if self.entity_type == "users":
            return await self._delete_user(resource_id)
        if self.entity_type == "groups":
            return await self._delete_group(resource_id)
        return

    async def _delete_user(self, user_id: str):
        del_q = [
            delete(models.user_emails).where(models.user_emails.c.userId == user_id),
            delete(models.users_groups).where(models.users_groups.c.userId == user_id),
            delete(models.users).where(models.users.c.id == user_id),
        ]
        async with self.engine.acquire() as conn:
            sel_q = select(models.users).where(models.users.c.id == user_id)
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
        del_q = delete(models.groups).where(models.groups.c.id == group_id)
        async with self.engine.acquire() as conn:
            sel_q = select(models.groups).where(models.groups.c.id == group_id)
            group = None
            async for row in conn.execute(sel_q):
                group = row
                break
            if not group:
                raise ResourceNotFound("Group", group_id)
            _ = await conn.execute(del_q)
        return {}

    async def parse_filter_expression(self, expr: str):
        pass

    async def clean_up_store(self):
        del_q = [
            delete(models.users),
            delete(models.groups),
            delete(models.user_emails),
            delete(models.users_groups),
        ]
        async with self.engine.acquire() as conn:
            for q in del_q:
                _ = await conn.execute(q)
        return
