scim_schema = "CREATE SCHEMA IF NOT EXISTS {};"
citext_extension = "CREATE EXTENSION IF NOT EXISTS citext WITH SCHEMA {};"

users_tbl = """
    CREATE TABLE IF NOT EXISTS {}.users (
        "id" CITEXT PRIMARY KEY,
        "externalId" CITEXT,
        "locale" CITEXT,
        "name" JSONB NOT NULL,
        "schemas" JSONB NOT NULL,
        "userName" CITEXT UNIQUE NOT NULL,
        "displayName" CITEXT NOT NULL,
        "customAttributes" JSONB,
        "active" BOOLEAN
    );
"""
users_idx = """
    CREATE INDEX IF NOT EXISTS users_username_index ON {}.users("userName");
"""

groups_tbl = """
    CREATE TABLE IF NOT EXISTS {}.groups (
        "id" CITEXT PRIMARY KEY,
        "displayName" CITEXT UNIQUE NOT NULL,
        "schemas" JSONB NOT NULL 
    );
"""
groups_idx = """
    CREATE INDEX IF NOT EXISTS groups_displayname_index ON {}.groups("displayName");
"""

users_groups_tbl = """
    CREATE TABLE IF NOT EXISTS {}.users_groups (
        "userId" CITEXT NOT NULL,
        "groupId" CITEXT NOT NULL,
        PRIMARY KEY("userId", "groupId")
    );
"""

user_emails_tbl = """
    CREATE TABLE IF NOT EXISTS {}.user_emails (
        "id" CITEXT PRIMARY KEY,
        "userId" CITEXT NOT NULL,
        "value" CITEXT NOT NULL,
        "primary" BOOLEAN DEFAULT TRUE,
        "type" CITEXT DEFAULT 'work'
    );
"""
user_emails_idx = """
    CREATE INDEX IF NOT EXISTS user_emails_value_index ON {}.user_emails("value");
"""

ddl_queries = [scim_schema, citext_extension, users_tbl, users_idx, groups_tbl, groups_idx, users_groups_tbl,
               user_emails_tbl, user_emails_idx]
