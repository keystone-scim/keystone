import pytest

from jsonpath_ng import parse
import pytest_check as check

from scim_2_api.models import DEFAULT_LIST_SCHEMA


class TestSpecUsersEndpoint:

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=0)
    async def test_status_code(users_endpoint_response):
        check.equal(users_endpoint_response.status, 200, "Failed to assert that the response status code was 200")

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=10)
    async def test_correct_schema(users_endpoint_response):
        body = await users_endpoint_response.json()
        check.is_in(
            DEFAULT_LIST_SCHEMA,
            body.get("schemas", []),
            f"Failed to assert that '{DEFAULT_LIST_SCHEMA}' was in body.schemas"
        )

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=20)
    @pytest.mark.parametrize("attribute", ["itemsPerPage", "startIndex", "totalResults"])
    async def test_pagination_attribute_is_int(users_endpoint_response, attribute):
        body = await users_endpoint_response.json()
        check.is_instance(
            body.get(attribute),
            int,
            f"Failed to assert that 'body.{attribute}' was an integer"
        )

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=30)
    @pytest.mark.parametrize("attribute",
                             ["Resources",
                              "Resources[0].id",
                              "Resources[0].name.familyName",
                              "Resources[0].name.givenName",
                              "Resources[0].userName",
                              "Resources[0].active",
                              "Resources[0].emails[0].value"])
    async def test_user_attribute_not_empty(users_endpoint_response, attribute):
        body = await users_endpoint_response.json()
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
