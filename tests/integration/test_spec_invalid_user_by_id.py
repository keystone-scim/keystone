import pytest

from jsonpath_ng import parse
import pytest_check as check

from keystone_scim.models import DEFAULT_ERROR_SCHEMA


class TestSpecInvalidUserById:

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=110)
    async def test_status_code(invalid_user_by_id_response):
        check.equal(invalid_user_by_id_response.status, 404, "Failed to assert that the response status code was 404")

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=120)
    @pytest.mark.parametrize("attribute", ["detail", "schemas", "status"])
    async def test_user_attribute_not_empty(invalid_user_by_id_response, attribute):
        body = await invalid_user_by_id_response.json()
        jsonpath_expr = parse(attribute)
        value = None
        for match in jsonpath_expr.find(body):
            value = match.value
            break
        body.get(attribute)
        check.is_not_none(
            value,
            f"Failed to assert that 'body.{attribute}' was not empty"
        )

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=130)
    async def test_correct_schema(invalid_user_by_id_response):
        body = await invalid_user_by_id_response.json()
        check.is_in(
            DEFAULT_ERROR_SCHEMA,
            body.get("schemas", []),
            f"Failed to assert that '{DEFAULT_ERROR_SCHEMA}' was in body.schemas"
        )
