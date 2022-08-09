import pytest

from jsonpath_ng import parse
import pytest_check as check

from keystone.models import DEFAULT_LIST_SCHEMA


class TestSpecRandomUserNonexistent:

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=140)
    async def test_status_code(random_user_nonexistent_response):
        check.equal(random_user_nonexistent_response.status, 200,
                    "Failed to assert that the response status code was 200")

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=150)
    async def test_correct_schema(random_user_nonexistent_response):
        body = await random_user_nonexistent_response.json()
        check.is_in(
            DEFAULT_LIST_SCHEMA,
            body.get("schemas", []),
            f"Failed to assert that '{DEFAULT_LIST_SCHEMA}' was in body.schemas"
        )

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=160)
    async def test_correct_total_result_count(random_user_nonexistent_response):
        body = await random_user_nonexistent_response.json()
        check.equal(
            0,
            body.get("totalResults"),
            "Failed to assert that body.id was equal to 0"
        )
