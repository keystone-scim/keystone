import pytest

from jsonpath_ng import parse
import pytest_check as check

from keystone.models import DEFAULT_LIST_SCHEMA


class TestSpecInvalidUserByUserName:

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=80)
    async def test_status_code(invalid_user_by_username_response):
        check.equal(invalid_user_by_username_response.status, 200,
                    "Failed to assert that the response status code was 200")

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=90)
    async def test_correct_schema(invalid_user_by_username_response):
        body = await invalid_user_by_username_response.json()
        check.is_in(
            DEFAULT_LIST_SCHEMA,
            body.get("schemas", []),
            f"Failed to assert that '{DEFAULT_LIST_SCHEMA}' was in body.schemas"
        )

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=100)
    async def test_correct_total_result_count(invalid_user_by_username_response):
        body = await invalid_user_by_username_response.json()
        check.equal(
            0,
            body.get("totalResults"),
            "Failed to assert that body.id was equal to 0"
        )
