import pytest

from keystone_scim.util.case_insensitive_dict import CaseInsensitiveDict


class TestCaseInsensitiveDict:

    @staticmethod
    @pytest.mark.asyncio
    async def test_compare_top_level_key(single_user):
        ci_user_dict = CaseInsensitiveDict(single_user)
        assert ci_user_dict.get("displayname") == single_user.get("displayName")

    @staticmethod
    @pytest.mark.asyncio
    async def test_build_deep(single_user):
        ci_user_dict = await CaseInsensitiveDict.build_deep(single_user)
        assert ci_user_dict.get("displayname") == single_user.get("displayName")
        assert ci_user_dict.get("NAME").get("gIvEnNaMe") == single_user.get("name").get("givenName")

        deep_dict = {
            "Foo": "bar",
            "Baz": {
                "Bar": "foo",
                "FOO": 1,
                "A1": {
                    "B1": True,
                },
            },
        }
        ci_deep_dict = await CaseInsensitiveDict.build_deep(deep_dict)
        assert 1 == ci_deep_dict["baz"]["foo"]
        assert ci_deep_dict["BAZ"]["a1"]["b1"] is True
        del ci_deep_dict["foo"]
        assert "Foo" not in ci_deep_dict
