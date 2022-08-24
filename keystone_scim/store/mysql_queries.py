# scim_schema = "CREATE SCHEMA IF NOT EXISTS `{}`;"

users_tbl = """
    CREATE TABLE IF NOT EXISTS `users` (
        `id` VARCHAR(256) PRIMARY KEY,
        `externalId` VARCHAR(1024),
        `locale` VARCHAR(64),
        `name` JSON NOT NULL,
        `schemas` JSON NOT NULL,
        `userName` VARCHAR(512) UNIQUE NOT NULL,
        `displayName` VARCHAR(1024) NOT NULL,
        `customAttributes` JSON,
        `active` BOOLEAN,
        INDEX USING BTREE (`userName`)
    );
"""

groups_tbl = """
    CREATE TABLE IF NOT EXISTS `groups` (
        `id` VARCHAR(256) PRIMARY KEY,
        `displayName` VARCHAR(512) UNIQUE NOT NULL,
        `schemas` JSON NOT NULL,
        INDEX USING BTREE (`displayName`)
    );
"""

users_groups_tbl = """
    CREATE TABLE IF NOT EXISTS `users_groups` (
        `userId` VARCHAR(256) NOT NULL,
        `groupId` VARCHAR(256) NOT NULL,
        PRIMARY KEY(`userId`, `groupId`)
    );
"""

user_emails_tbl = """
    CREATE TABLE IF NOT EXISTS `user_emails` (
        `id` VARCHAR(256) PRIMARY KEY,
        `userId` VARCHAR(256) NOT NULL,
        `value` VARCHAR(512) NOT NULL,
        `primary` BOOLEAN DEFAULT TRUE,
        `type` VARCHAR(128) DEFAULT 'work',
        INDEX USING BTREE (`value`)
    );
"""

ddl_queries = [users_tbl, groups_tbl, users_groups_tbl, user_emails_tbl]
