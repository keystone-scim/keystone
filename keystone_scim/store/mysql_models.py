import sqlalchemy as sa
from sqlalchemy.dialects.mysql import JSON

from keystone_scim.util.config import Config

metadata = sa.MetaData()

CONFIG = Config()
_schema = CONFIG.get("store.mysql.schema", "public")


users = sa.Table(
    "users", metadata,
    sa.Column("id", sa.VARCHAR, primary_key=True),
    sa.Column("externalId", sa.VARCHAR),
    sa.Column("locale", sa.VARCHAR),
    sa.Column("name", JSON, nullable=False),
    sa.Column("schemas", JSON, nullable=False),
    sa.Column("userName", sa.VARCHAR, nullable=False),
    sa.Column("displayName", sa.VARCHAR, nullable=False),
    sa.Column("active", sa.Boolean, default=True),
    sa.Column("customAttributes", JSON)
)

groups = sa.Table(
    "groups", metadata,
    sa.Column("id", sa.VARCHAR, primary_key=True),
    sa.Column("displayName", sa.VARCHAR, nullable=False),
    sa.Column("schemas", JSON, nullable=False)
)

users_groups = sa.Table(
    "users_groups", metadata,
    sa.Column("userId", sa.VARCHAR, sa.ForeignKey("users.id")),
    sa.Column("groupId", sa.VARCHAR, sa.ForeignKey("groups.id"))
)

user_emails = sa.Table(
    "user_emails", metadata,
    sa.Column("id", sa.VARCHAR, primary_key=True),
    sa.Column("userId", sa.VARCHAR, sa.ForeignKey("users.id")),
    sa.Column("primary", sa.Boolean, default=True),
    sa.Column("value", sa.VARCHAR),
    sa.Column("type", sa.VARCHAR)
)
