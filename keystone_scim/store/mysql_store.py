import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import aiomysql
import pymysql.cursors
from aiomysql.sa import create_engine
from aiomysql.sa.result import RowProxy
from scim2_filter_parser.queries import SQLQuery
from sqlalchemy import delete, insert, select, text, update, and_, or_
from sqlalchemy.sql.base import ImmutableColumnCollection
from sqlalchemy.sql.elements import TextClause

from keystone_scim.models.user import DEFAULT_USER_SCHEMA
from keystone_scim.store import mysql_models as tbl
from keystone_scim.store import RDBMSStore
from keystone_scim.store.mysql_queries import ddl_queries
from keystone_scim.util.config import Config
from keystone_scim.util.exc import ResourceNotFound

CONFIG = Config()
LOGGER = logging.getLogger(__name__)
CONN_REFRESH_INTERVAL_SEC = 1 * 60 * 60


def get_conn_args(**kwargs):
    conn_args = {**kwargs}
    args = ["host", "port", "user", "password", "database", "ssl"]
    for arg in args:
        if CONFIG.get(f"store.mysql.{arg}"):
            conn_args[arg] = CONFIG.get(f"store.mysql.{arg}")
    if conn_args.get("ssl") is not None:
        conn_args["ssl_disabled"] = True
        del conn_args["ssl"]
    return conn_args


def set_up_schema(**kwargs):
    conn_args = get_conn_args(**kwargs)
    conn = pymysql.connect(cursorclass=pymysql.cursors.DictCursor, **conn_args)
    with conn:
        with conn.cursor() as cursor:
            for q in ddl_queries:
                cursor.execute(q)
        conn.commit()


async def _transform_group(group_record: RowProxy) -> Dict:
    members = []
    if group_record.members:
        members = json.loads(group_record.members)
        if len(members) > 0 and not isinstance(members[0], dict):
            members = []

    return {
        "id": group_record.id,
        "displayName": group_record.displayName,
        "members": [m for m in members if m.get("value")],
    }


async def _transform_user(user_record: RowProxy) -> Dict:
    groups = []
    if user_record.groups:
        groups = json.loads(user_record.groups)
        if len(groups) > 0 and not isinstance(groups[0], dict):
            groups = []
    emails = json.loads(user_record.emails)
    return {
        "id": user_record.id,
        "userName": user_record.userName,
        "externalId": user_record.externalId,
        "schemas": user_record.schemas,
        "locale": user_record.locale,
        "name": user_record.name,
        "displayName": user_record.displayName,
        "active": user_record.active,
        "emails": emails,
        "groups": [g for g in groups if g.get("displayName")],
        **(user_record.customAttributes or {})
    }


class MySqlStore(RDBMSStore):
    engine: aiomysql.sa.Engine = None
    entity_type: str
    last_conn = None

    user_attr_map = {
        ("userName", None, None): "`users`.`userName`",
        ("displayName", None, None): "`users`.`displayName`",
        ("externalId", None, None): "`users`.`externalId`",
        ("id", None, None): "`users`.`id`",
        ("active", None, None): "`users`.`active`",
        ("locale", None, None): "`users`.`locale`",
        ("name", None, None): "`users`.`name`.`formatted`",
        ("emails", None, None): "`user_emails`.`value`",
        ("emails", "value", None): "`user_emails`.`value`",
        ("value", None, None): "`users_groups`.`userId`",
    }

    group_attr_map = {
        ("displayName", None, None): "`groups`.`displayName`",
        ("id", None, None): "`groups`.id",
        ("members", "value", None): "`users_groups`.`userId`",
        ("members", None, None): "`users_groups`.`userId`",
        ("members", "display", None): "`users`.`userName`",
    }

    def __init__(self, entity_type: str, **conn_args):
        self.entity_type = entity_type
        self.conn_args = conn_args

    async def get_engine(self):
        if not self.engine or not self.last_conn or (
                datetime.now() - self.last_conn).total_seconds() > CONN_REFRESH_INTERVAL_SEC:
            self.last_conn = datetime.now()
            conn_args = get_conn_args(**self.conn_args)
            conn_args["db"] = conn_args.get("database")
            if conn_args.get("ssl_disabled") is not None:
                del conn_args["ssl_disabled"]
            del conn_args["database"]
            self.engine = await create_engine(**conn_args)
        return self.engine

    async def term_connection(self):
        engine = await self.get_engine()
        if engine:
            engine.close()
            return await engine.wait_closed()

    async def _get_user_by_id(self, user_id: str) -> Dict:
        em_agg = text("""
                    JSON_ARRAYAGG(JSON_OBJECT(
                        'value', `user_emails`.`value`,
                        'primary', CAST(`user_emails`.`primary` is true as JSON),
                        'type', `user_emails`.`type`
                    )) as `emails`
                """)
        gr_agg = text("""
                    JSON_ARRAYAGG(JSON_OBJECT('displayName', `groups`.`displayName`)) as `groups`
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
                    JSON_ARRAYAGG(JSON_OBJECT(
                        'display', `users`.`userName`,
                        'value', `users`.`id`
                    )) as `members`
                """)
        q = select([tbl.groups, mem_agg]). \
            join(tbl.users_groups, tbl.groups.c.id == tbl.users_groups.c.groupId, isouter=True). \
            join(tbl.users, tbl.users.c.id == tbl.users_groups.c.userId, isouter=True). \
            where(tbl.groups.c.id == group_id). \
            group_by(text("1,2,3"))
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            async with conn.begin() as transaction:
                entity_record = None
                async for row in conn.execute(q):
                    entity_record = row
                    break
                if not entity_record:
                    raise ResourceNotFound("Group", group_id)
                await transaction.commit()
        return await _transform_group(entity_record)

    async def get_by_id(self, resource_id: str):
        if self.entity_type == "users":
            return await self._get_user_by_id(resource_id)
        if self.entity_type == "groups":
            return await self._get_group_by_id(resource_id)

    async def _get_where_clause_from_filter(self, _filter: str, attr_map: Dict)\
            -> Tuple[Optional[TextClause], Dict]:
        if not _filter:
            return None, {}
        parsed_q = SQLQuery(_filter, self.entity_type, attr_map)
        where = parsed_q.where_sql
        parsed_params = parsed_q.params_dict
        sqla_params = {}
        for k in parsed_params.keys():
            sqla_params[f"param_{k}"] = parsed_params[k]
            where = where.replace(f"{{{k}}}", f":param_{k}")
        return text(where), sqla_params

    async def _search_users(self, _filter: str, start_index: int = 1, count: int = 100) -> tuple[list[Dict], int]:
        where_clause, sqla_params = await self._get_where_clause_from_filter(_filter, self.user_attr_map)
        em_agg = text("""
                    JSON_ARRAYAGG(JSON_OBJECT(
                        'value', `user_emails`.`value`,
                        'primary', CAST(`user_emails`.`primary` is true as JSON),
                        'type', `user_emails`.`type`
                    )) as `emails`
        """)
        gr_agg = text("""
            JSON_ARRAYAGG(JSON_OBJECT('displayName', `groups`.`displayName`)) as `groups`
        """)
        ct = text("count(*) OVER() as `total`")
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            q = select([tbl.users, em_agg, gr_agg, ct]). \
                join(tbl.user_emails, tbl.users.c.id == tbl.user_emails.c.userId, isouter=True). \
                join(tbl.users_groups, tbl.users.c.id == tbl.users_groups.c.userId, isouter=True). \
                join(tbl.groups, tbl.groups.c.id == tbl.users_groups.c.groupId, isouter=True)
            if where_clause is not None:
                q = q.where(where_clause)
            q = q.group_by(text("1,2,3,4,5,6,7,8,9")).offset(start_index - 1).limit(count)
            users = []
            total = 0
            async for row in conn.execute(q, **sqla_params):
                users.append(await _transform_user(row))
                total = row.total

        return users, total

    async def _search_groups(self, _filter: str, start_index: int = 1, count: int = 100) -> tuple[list[Dict], int]:
        where_clause, sqla_params = await self._get_where_clause_from_filter(_filter, self.group_attr_map)
        ct = text("count(*) OVER() as `total`")
        q = select([tbl.groups, text("CAST('[]' AS JSON) as members"), ct]). \
            join(tbl.users_groups, tbl.groups.c.id == tbl.users_groups.c.groupId, isouter=True). \
            join(tbl.users, tbl.users.c.id == tbl.users_groups.c.userId, isouter=True)

        if where_clause is not None:
            q = q.where(where_clause)
        q = q.group_by(text("1,2,3,4")).offset(start_index - 1).limit(count)
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            groups = []
            total = 0
            async for row in conn.execute(q, **sqla_params):
                groups.append(await _transform_group(row))
                total = row.total
        return groups, total

    async def search(self, _filter: str, start_index: int = 1, count: int = 100) -> tuple[list[Dict], int]:
        if self.entity_type == "users":
            return await self._search_users(_filter, start_index, count)
        if self.entity_type == "groups":
            return await self._search_groups(_filter, start_index, count)

    async def update(self, resource_id: str, **kwargs: Dict):
        sanitized = await self._sanitize(kwargs)
        if self.entity_type == "users":
            return await self._update_user(resource_id, **sanitized)
        if self.entity_type == "groups":
            return await self._update_group(resource_id, **sanitized)

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
            async with conn.begin() as transaction:
                _ = await conn.execute(q)
                await transaction.commit()
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
                async with conn.begin() as transaction:
                    _ = await conn.execute(del_emails_q)
                    _ = await conn.execute(ins_emails_q)
                    await transaction.commit()
        return await self._get_user_by_id(user_id)

    async def _update_group(self, group_id: str, **kwargs: Dict) -> Dict:
        if "id" in kwargs:
            del kwargs["id"]
        q = update(tbl.groups).where(tbl.groups.c.id == group_id).values(**kwargs)
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            async with conn.begin() as transaction:
                _ = await conn.execute(q)
                await transaction.commit()
        return await self._get_group_by_id(group_id)

    async def create(self, resource: Dict):
        sanitized = await self._sanitize(resource)
        if self.entity_type == "users":
            return await self._create_user(sanitized)
        if self.entity_type == "groups":
            return await self._create_group(sanitized)

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
            async with conn.begin() as transaction:
                _ = await conn.execute(insert_group)
                if insert_members is not None:
                    _ = await conn.execute(insert_members)
                await transaction.commit()

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
        emails = resource.get("emails", [{"primary": True, "value": resource.get("userName"), "type": "work"}])
        insert_emails = insert(tbl.user_emails).values([
            {
                "id": str(uuid.uuid4()),
                "userId": user_id,
                "primary": email.get("primary", True),
                "value": email.get("value"),
                "type": email.get("type")
            } for email in emails
        ])
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            async with conn.begin() as transaction:
                _ = await conn.execute(insert_user)
                _ = await conn.execute(insert_emails)
                await transaction.commit()
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
            async with conn.begin() as transaction:
                sel_q = select(tbl.users).where(tbl.users.c.id == user_id)
                user = None
                async for row in conn.execute(sel_q):
                    user = row
                    break
                if not user:
                    raise ResourceNotFound("User", user_id)
                for q in del_q:
                    _ = await conn.execute(q)
                transaction.commit()
        return {}

    async def _delete_group(self, group_id: str):
        del_q = delete(tbl.groups).where(tbl.groups.c.id == group_id)
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            async with conn.begin() as transaction:
                sel_q = select(tbl.groups).where(tbl.groups.c.id == group_id)
                group = None
                async for row in conn.execute(sel_q):
                    group = row
                    break
                if not group:
                    raise ResourceNotFound("Group", group_id)
                _ = await conn.execute(del_q)
                await transaction.commit()
        return {}

    async def remove_users_from_group(self, user_ids: List[str], group_id: str):
        user_id_conditions = []
        for user_id in user_ids:
            user_id_conditions.append(tbl.users_groups.c.userId == user_id)
        q = delete(tbl.users_groups).where(
            and_(
                tbl.users_groups.c.groupId == group_id,
                or_(*user_id_conditions)
            )
        )
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            async with conn.begin() as transaction:
                _ = await conn.execute(q)
                await transaction.commit()
        return

    async def add_user_to_group(self, user_id: str, group_id: str):
        check_q = select(tbl.users_groups).where(
            and_(tbl.users_groups.c.userId == user_id, tbl.users_groups.c.groupId == group_id)
        )
        insert_q = insert(tbl.users_groups).values(userId=user_id, groupId=group_id)
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            async with conn.begin() as transaction:
                async for row in await conn.execute(check_q):
                    return
                _ = await conn.execute(insert_q)
                await transaction.commit()
        return

    async def set_group_members(self, user_ids: List[str], group_id: str):
        delete_q = delete(tbl.users_groups).where(tbl.users_groups.c.groupId == group_id)
        insert_q = insert(tbl.users_groups).values(
            [{"userId": uid, "groupId": group_id} for uid in user_ids]
        )
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            async with conn.begin() as transaction:
                _ = await conn.execute(delete_q)
                _ = await conn.execute(insert_q)
                await transaction.commit()
        return

    async def search_members(self, _filter: str, group_id: str):
        parsed_q = SQLQuery(_filter, "users_groups", self.user_attr_map)
        where = parsed_q.where_sql
        parsed_params = parsed_q.params_dict
        sqla_params = {}
        for k in parsed_params.keys():
            sqla_params[f"param_{k}"] = parsed_params[k]
            where = where.replace(f"{{{k}}}", f":param_{k}")
        q = select([tbl.users_groups]).join(tbl.users, tbl.users.c.id == tbl.users_groups.c.userId). \
            where(and_(tbl.users_groups.c.groupId == group_id, text(where)))
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            res = []
            async for row in await conn.execute(q, **sqla_params):
                res.append({"value": row.userId})
        return res

    async def clean_up_store(self) -> None:
        engine = await self.get_engine()
        async with engine.acquire() as conn:
            async with conn.begin() as transaction:
                _ = await conn.execute(delete(tbl.users))
                _ = await conn.execute(delete(tbl.user_emails))
                _ = await conn.execute(delete(tbl.users_groups))
                _ = await conn.execute(delete(tbl.groups))
                await transaction.commit()
        return
