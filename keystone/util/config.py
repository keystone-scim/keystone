import logging
import os

from keystone.util import ThreadSafeSingleton

from schema import Optional, Schema
import yaml


LOGGER = logging.getLogger(__name__)
SCHEMA = Schema({
    Optional("store", default={}): Schema({
        Optional("type", default="InMemory"): str,
        Optional("cosmos", default=None): Schema({
            Optional("tenant_id"): str,
            Optional("client_id"): str,
            Optional("client_secret"): str,
            Optional("account_uri"): str,
            Optional("account_key"): str,
            Optional("db_name", default="scim_2_db"): str,
        }),
        Optional("pg", default=None): Schema({
            Optional("host"): str,
            Optional("port", default=5432): int,
            Optional("ssl_mode", default="require"): str,
            Optional("username"): str,
            Optional("password"): str,
            Optional("database", default="postgres"): str,
            Optional("schema", default="public"): str,
        }),
        Optional("mongo", default=None): Schema({
            Optional("host"): str,
            Optional("port", default=27017): int,
            Optional("username"): str,
            Optional("password"): str,
            Optional("database", default="scim2Db"): str,
            Optional("tls", default=True): bool,
            Optional("replica_set", default=True): str,
            Optional("dsn"): str,
        })
    }),
    Optional("authentication", default={}): Schema({
        Optional("akv", default={}): Schema({
            Optional("vault_name"): str,
            Optional("secret_name", default="scim-2-api-token"): str,
            Optional("force_create", default=False): bool,
            Optional("credentials_client", default="default"): str,
        }),
        Optional("secret"): str,
    }),
})


# pylint: disable=too-few-public-methods
class Config(metaclass=ThreadSafeSingleton):
    schema = SCHEMA

    def __init__(self, config_file=None):
        if not config_file:
            config_file = os.environ.get("CONFIG_PATH", "config.yaml")
        path = os.path.normpath(config_file)

        LOGGER.debug("Attempting to load config from file: %s", path)
        try:
            with open(path, "r", encoding="utf-8") as config:
                data = yaml.safe_load(config.read())
            self.data = self.schema.validate(data)
            LOGGER.debug("Loaded config data: %s", self.data)
        except FileNotFoundError:
            LOGGER.warning("Config file not found: %s. This means that all "
                           "configuration keys are expected to be found in environment variables.", path)
            self.data = {}

    def get(self, key, default_value=None):
        """
        :param key:           The configuration key to fetch, in dot-separated format
        :param default_value: An optional default value in case the key path doesn't exist
        :return:              Any
        """

        env_var_name = key.upper().replace(".", "_")
        env_var = os.environ.get(env_var_name)
        if env_var:
            return env_var

        value = self.data
        keys = key.split(".")
        for index, current_key in enumerate(keys, start=1):
            try:
                if not isinstance(value, dict) and len(keys) == index:
                    return value if value is not None else default_value
                value = value[current_key]
            except KeyError:
                return default_value
        return value

    @property
    def __dict__(self):
        return self.data
