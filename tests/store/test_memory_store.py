import pytest

from azure_ad_scim_2_api.store.memory_store import MemoryStore


class TestMemoryStore:

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_equal_filter():
        store = MemoryStore()
        operation = await store.parse_operation("userName Eq 'john.doe@company.com'")
        func = operation.get("func")
        pred = operation.get("pred")
        assert func("john.doe@company.com", pred)
        assert not func("jane.doe@company.com", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_not_equal_filter():
        store = MemoryStore()
        operation = await store.parse_operation("userName Ne 'john.doe@company.com'")
        func = operation.get("func")
        pred = operation.get("pred")
        assert func("jane.doe@company.com", pred)
        assert not func("John.Doe@Company.com", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_contains_filter():
        store = MemoryStore()
        operation = await store.parse_operation("userName cO 'john.doe'")
        func = operation.get("func")
        pred = operation.get("pred")
        assert func("john.doe@company.com", pred)
        assert not func("microsoft.com", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_starts_with_filter():
        store = MemoryStore()
        operation = await store.parse_operation("userName Sw 'john.doe'")
        func = operation.get("func")
        pred = operation.get("pred")
        assert func("John.Doe@Company.com", pred)
        assert not func("Company.com", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_ends_with_filter():
        store = MemoryStore()
        operation = await store.parse_operation("userName ew 'microsoft.com'")
        func = operation.get("func")
        pred = operation.get("pred")
        assert func("John.Doe@Microsoft.com", pred)
        assert not func("company.com", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_greater_than_filter():
        store = MemoryStore()
        operation = await store.parse_operation("userName gt 'b'")
        func = operation.get("func")
        pred = operation.get("pred")
        assert func("c", pred)
        assert not func("b", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_greater_than_or_equal_to_filter():
        store = MemoryStore()
        operation = await store.parse_operation("userName ge 'b'")
        func = operation.get("func")
        pred = operation.get("pred")
        assert func("c", pred)
        assert func("b", pred)
        assert not func("a", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_lower_than_filter():
        store = MemoryStore()
        operation = await store.parse_operation("userName lt 'c'")
        func = operation.get("func")
        pred = operation.get("pred")
        assert func("b", pred)
        assert not func("c", pred)
        assert not func("d", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_lower_than_or_equal_to_filter():
        store = MemoryStore()
        operation = await store.parse_operation("userName le 'c'")
        func = operation.get("func")
        pred = operation.get("pred")
        assert func("b", pred)
        assert func("c", pred)
        assert not func("d", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_invalid_operator():
        store = MemoryStore()
        exc_thrown = False
        try:
            _ = await store.parse_operation("userName equals 'c'")
        except ValueError as e:
            assert "Invalid operator: equals" == str(e)
            exc_thrown = True
        assert exc_thrown

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_invalid_operation():
        store = MemoryStore()
        exc_thrown = False
        try:
            _ = await store.parse_operation("userName 'c' eq")
        except ValueError as e:
            assert "Could not parse operation" == str(e)
            exc_thrown = True
        assert exc_thrown
