import pytest

import pytest_check as check


class TestSpecFailureOnDuplicateUserCreation:

    @staticmethod
    @pytest.mark.asyncio
    @pytest.mark.run(order=230)
    async def test_status_code(create_realistic_user_response):
        check.equal(
            create_realistic_user_response.status,
            409,
            "Failed to assert that the response status code was 409"
        )
