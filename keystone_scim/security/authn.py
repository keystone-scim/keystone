import logging
import uuid

from aiohttp.typedefs import Handler
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError
from azure.identity import AzureCliCredential, DefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient, KeyVaultSecret

from keystone_scim.util import ThreadSafeSingleton
from keystone_scim.util.config import Config
from keystone_scim.util.exc import UnauthorizedRequest

from aiohttp import web


CONFIG = Config()
LOGGER = logging.getLogger(__name__)


class SCIMTokenClient(metaclass=ThreadSafeSingleton):

    secret: str

    def __init__(self):
        self.secret = self._fetch_secret()

    @staticmethod
    def get_secret_client():
        key_vault_name = CONFIG.get("authentication.akv.vault_name")
        vault_url = f"https://{key_vault_name}.vault.azure.net/"
        credentials_client_type = CONFIG.get("authentication.akv.credentials_client")
        if credentials_client_type == "cli":
            credential = AzureCliCredential()
        else:
            credential = DefaultAzureCredential()
        return SecretClient(vault_url=vault_url, credential=credential)

    def _fetch_secret(self):
        secret_from_config = CONFIG.get("authentication.secret")
        if secret_from_config:
            return secret_from_config

        secret_client = SCIMTokenClient.get_secret_client()
        secret_name = CONFIG.get("authentication.akv.secret_name")
        try:
            secret: KeyVaultSecret = secret_client.get_secret(name=secret_name)
            LOGGER.info("SCIM 2.0 API token retrieved from Azure Key Vault")
        except ResourceNotFoundError:
            force_create = CONFIG.get("authentication.akv.force_create")
            if force_create:
                secret_value = str(uuid.uuid4())
                secret: KeyVaultSecret = secret_client.set_secret(secret_name, secret_value)
                LOGGER.info("A new SCIM 2.0 API token was created with the following value: %s", secret_value)
                return secret.value
            raise
        except ClientAuthenticationError:
            LOGGER.error("Token could not be retrieved from Azure Key vault - authentication error")
            raise
        return secret.value


@web.middleware
async def bearer_token_check(request: web.Request, handler: Handler):
    scim_token_client = SCIMTokenClient()
    authz_header: str = request.headers.get("Authorization")
    if not authz_header:
        raise UnauthorizedRequest
    try:
        token = authz_header.split("Bearer ")[-1]
    except (AttributeError, IndexError):
        raise UnauthorizedRequest
    if token != scim_token_client.secret:
        raise UnauthorizedRequest
    return await handler(request)
