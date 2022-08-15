import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from keystone.util.config import Config

metadata = sa.MetaData()

CONFIG = Config()
_schema = CONFIG.get("store.pg_schema", "public")


users = sa.Table(
    "users", metadata,
    sa.Column("id", sa.Text, primary_key=True),
    sa.Column("externalId", sa.Text),
    sa.Column("locale", sa.Text),
    sa.Column("name", JSONB, nullable=False),
    sa.Column("schemas", JSONB, nullable=False),
    sa.Column("userName", sa.Text, nullable=False),
    sa.Column("displayName", sa.Text, nullable=False),
    sa.Column("active", sa.Boolean, default=True),
    sa.Column("customAttributes", JSONB),
    schema=_schema
)

groups = sa.Table(
    "groups", metadata,
    sa.Column("id", sa.Text, primary_key=True),
    sa.Column("displayName", sa.Text, nullable=False),
    sa.Column("schemas", JSONB, nullable=False),
    schema=_schema
)

users_groups = sa.Table(
    "users_groups", metadata,
    sa.Column("userId", sa.Text, sa.ForeignKey("users.id")),
    sa.Column("groupId", sa.Text, sa.ForeignKey("groups.id")),
    schema=_schema
)

user_emails = sa.Table(
    "user_emails", metadata,
    sa.Column("id", sa.Text, primary_key=True),
    sa.Column("userId", sa.Text, sa.ForeignKey("users.id")),
    sa.Column("primary", sa.Boolean, default=True),
    sa.Column("value", sa.Text),
    sa.Column("type", sa.Text),
    schema=_schema
)
