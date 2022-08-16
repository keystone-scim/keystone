import pytest

from keystone.util.exc import ResourceNotFound


class TestPostgreSQLStore:

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_user(postgresql_stores):
        user_store, _ = postgresql_stores
        exc_thrown = False
        try:
            _ = await user_store.get_by_id("I do not exist")
        except ResourceNotFound:
            exc_thrown = True
        assert exc_thrown

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_user_2(postgresql_stores):
        user_store, _ = postgresql_stores
        exc_thrown = False
        try:
            _ = await user_store.get_by_id("I do not exist")
        except ResourceNotFound:
            exc_thrown = True
        assert exc_thrown
