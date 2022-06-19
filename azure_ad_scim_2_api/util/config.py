import logging
import os

from azure_ad_scim_2_api.util import ThreadSafeSingleton

from schema import Optional, Schema
import yaml


LOGGER = logging.getLogger(__name__)
SCHEMA = Schema({
    Optional("store", default={}): Schema({
        Optional("type", default="AzureAD"): str,
        Optional("tenant_id"): str,
        Optional("client_id"): str,
        Optional("client_secret"): str,
    }),
    Optional("provisioning", default={}): Schema({
        Optional("groups", default=True): bool,
        Optional("users_as_guests", default=False): bool,
        Optional("user_type_schema"): str,
    }),
})


# pylint: disable=too-few-public-methods
class Config(metaclass=ThreadSafeSingleton):
    schema = SCHEMA

    def __init__(self, config_file=None):
        if not config_file:
            config_file = os.environ.get("CONFIG_PATH", "config.yaml")
        path = os.path.normpath(config_file)

        LOGGER.debug("Loading config from file: %s", path)
        try:
            with open(path, "r", encoding="utf-8") as config:
                data = yaml.safe_load(config.read())
        except FileNotFoundError:
            LOGGER.exception("Config file not found")
            raise

        self.data = self.schema.validate(data)
        LOGGER.debug("Loaded config data: %s", self.data)

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
