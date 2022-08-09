users_tbl = """
    CREATE TABLE IF NOT EXISTS {}.users (
        "id" TEXT PRIMARY KEY,
        "externalId" TEXT,
        "locale" TEXT,
        "name" JSONB NOT NULL,
        "schemas" JSONB NOT NULL,
        "userName" TEXT UNIQUE NOT NULL,
        "displayName" TEXT NOT NULL,
        "customAttributes" JSONB,
        "active" BOOLEAN
    );
"""
users_idx = """
    CREATE INDEX IF NOT EXISTS users_username_index ON {}.users("userName");
"""

groups_tbl = """
    CREATE TABLE IF NOT EXISTS {}.groups (
        "id" TEXT PRIMARY KEY,
        "displayName" TEXT NOT NULL,
        "schemas" JSONB NOT NULL 
    );
"""
groups_idx = """
    CREATE INDEX IF NOT EXISTS groups_displayname_index ON {}.groups("displayName");
"""

users_groups_tbl = """
    CREATE TABLE IF NOT EXISTS {}.users_groups (
        "userId" TEXT NOT NULL,
        "groupId" TEXT NOT NULL,
        PRIMARY KEY("userId", "groupId")
    );
"""

user_emails_tbl = """
    CREATE TABLE IF NOT EXISTS {}.user_emails (
        "id" TEXT PRIMARY KEY,
        "userId" TEXT NOT NULL,
        "value" TEXT NOT NULL,
        "primary" BOOLEAN DEFAULT TRUE,
        "type" TEXT DEFAULT 'work'
    );
"""
user_emails_idx = """
    CREATE INDEX IF NOT EXISTS user_emails_value_index ON {}.user_emails("value");
"""

# custom_user_attributes = """
#     CREATE TABLE IF NOT EXISTS {}.custom_user_attributes (
#         "userId" TEXT NOT NULL,
#         "schema" TEXT NOT NULL,
#         "value" JSONB NOT NULL,
#         PRIMARY KEY("userId", "schema")
#     );
# """

ddl_queries = [users_tbl, users_idx, groups_tbl, groups_idx, users_groups_tbl,
               user_emails_tbl, user_emails_idx]
