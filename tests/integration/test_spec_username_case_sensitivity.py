import pytest

from jsonpath_ng import parse
import pytest_check as check

from keystone.models import DEFAULT_LIST_SCHEMA


class TestSpecUsernameCaseSensitivity:

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=240)
    async def test_status_code(username_case_sensitivity_response):
        check.equal(username_case_sensitivity_response.status, 200,
                    "Failed to assert that the response status code was 200")

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=250)
    @pytest.mark.parametrize("attribute, expected_value",
                             [("Resources[0].name.familyName", "Gonzales"),
                              ("Resources[0].name.givenName", "Daniel"),
                              ("Resources[0].userName", "dgonzales@company.com")])
    async def test_user_attribute_has_expected_value(username_case_sensitivity_response, attribute, expected_value):
        body = await username_case_sensitivity_response.json()
        print(body)
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
