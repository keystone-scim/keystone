import pytest

from jsonpath_ng import jsonpath, parse
import pytest_check as check

from keystone_scim.models import DEFAULT_LIST_SCHEMA
from keystone_scim.models.user import DEFAULT_USER_SCHEMA


class TestSpecUsersEndpoint:

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=40)
    async def test_status_code(user_by_id_endpoint_response):
        check.equal(
            user_by_id_endpoint_response.status,
            200,
            "Failed to assert that the response status code was 200"
        )

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=50)
    async def test_correct_schema(user_by_id_endpoint_response):
        body = await user_by_id_endpoint_response.json()
        check.is_in(
            DEFAULT_USER_SCHEMA,
            body.get("schemas", []),
            f"Failed to assert that '{DEFAULT_USER_SCHEMA}' was in body.schemas"
        )

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=60)
    async def test_matching_user_id(user_by_id_endpoint_response, initial_user):
        body = await user_by_id_endpoint_response.json()
        check.equal(
            initial_user.get("id"),
            body.get("id"),
            f"Failed to assert that body.id was equal to '{initial_user.get('id')}'"
        )

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=70)
    @pytest.mark.parametrize("attribute",
                             ["id",
                              "name.familyName",
                              "name.givenName",
                              "userName",
                              "active",
                              "emails[0].value"])
    async def test_user_attribute_not_empty(user_by_id_endpoint_response, attribute):
        body = await user_by_id_endpoint_response.json()
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
