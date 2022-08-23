import pytest

from jsonpath_ng import parse
import pytest_check as check

from keystone_scim.models import DEFAULT_LIST_SCHEMA


class TestSpecVerifyUserCreated:

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=210)
    async def test_status_code(verify_user_created_response):
        check.equal(verify_user_created_response.status, 200, "Failed to assert that the response status code was 200")

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=220)
    @pytest.mark.parametrize("attribute, expected_value",
                             [("name.familyName", "Gonzales"),
                              ("name.givenName", "Daniel"),
                              ("userName", "dgonzales@company.com")])
    async def test_user_attribute_has_expected_value(verify_user_created_response, attribute, expected_value):
        body = await verify_user_created_response.json()
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
