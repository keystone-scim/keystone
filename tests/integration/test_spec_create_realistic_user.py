import pytest

from jsonpath_ng import jsonpath, parse
import pytest_check as check

from keystone.models import DEFAULT_LIST_SCHEMA
from keystone.models.user import DEFAULT_USER_SCHEMA


class TestSpecCreateRealisticUser:

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=170)
    async def test_status_code(create_realistic_user_response):
        check.equal(
            create_realistic_user_response.status,
            201,
            "Failed to assert that the response status code was 201"
        )

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=180)
    async def test_correct_schema(create_realistic_user_response):
        body = await create_realistic_user_response.json()
        check.is_in(
            DEFAULT_USER_SCHEMA,
            body.get("schemas", []),
            f"Failed to assert that '{DEFAULT_USER_SCHEMA}' was in body.schemas"
        )

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=190)
    @pytest.mark.parametrize("attribute, expected_value",
                             [("active", True),
                              ("name.familyName", "Gonzales"),
                              ("name.givenName", "Daniel"),
                              ("userName", "dgonzales@company.com")])
    async def test_user_attribute_has_expected_value(create_realistic_user_response, attribute, expected_value):
        body = await create_realistic_user_response.json()
        jsonpath_expr = parse(attribute)
        value = None
        for match in jsonpath_expr.find(body):
            value = match.value
            break
        body.get(attribute)
        check.equal(
            expected_value,
            value,
            f"Failed to assert that 'body.{attribute}' is equal to '{expected_value}'"
        )

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=200)
    @pytest.mark.parametrize("attribute", ["id", "userName"])
    async def test_user_attribute_not_empty(create_realistic_user_response, attribute):
        body = await create_realistic_user_response.json()
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
