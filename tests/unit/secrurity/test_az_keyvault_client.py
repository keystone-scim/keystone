import pytest

from azure.core.exceptions import ResourceNotFoundError

from keystone_scim.security.authn import SCIMTokenClient
from keystone_scim.util.config import Config


class TestSCIMTokenClient:

    @staticmethod
    @pytest.mark.asyncio
    async def test_fetch_secret_success(monkeypatch):
        config = Config()

        class MockSecretValue:
            value = "not very secret"

        class MockSecretClient:

            def get_secret(self, name):
                return MockSecretValue()

            def set_secret(self, name, value):
                return

        def get_secret_client():
            return MockSecretClient()

        monkeypatch.setattr(SCIMTokenClient, "get_secret_client", get_secret_client)
        scim_token_client = SCIMTokenClient()
        assert "not very secret" == scim_token_client.secret

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_secret_if_nonexistent(monkeypatch):
        class MockSecretValue:
            value = "not very secret"

        class MockSecretClient:

            def get_secret(self, name):
                raise ResourceNotFoundError

            def set_secret(self, name, value):
                return MockSecretValue

        def get_secret_client():
            return MockSecretClient()

        monkeypatch.setattr(SCIMTokenClient, "get_secret_client", get_secret_client)
        scim_token_client = SCIMTokenClient()
        assert "not very secret" == scim_token_client.secret
