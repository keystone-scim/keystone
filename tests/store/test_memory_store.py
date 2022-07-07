import asyncio
import random
from typing import Dict

import pytest
from scim2_filter_parser.parser import SCIMParserError

from azure_ad_scim_2_api.util.case_insensitive_dict import CaseInsensitiveDict
from azure_ad_scim_2_api.util.exc import ResourceNotFound, ResourceAlreadyExists


class TestMemoryStore:

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_success(single_user, memory_store):
        await memory_store.create(single_user)
        expected_username = single_user.get("username")
        assert single_user.get("id") in memory_store.resource_db
        user_from_store = memory_store.resource_db[single_user.get("id")]
        assert expected_username == user_from_store.get("username")
        assert not user_from_store.get("password")

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_duplicate_resource_fails(single_user, memory_store):
        await memory_store.create(single_user)
        assert single_user.get("id") in memory_store.resource_db
        exc_raised = False
        try:
            await memory_store.create(single_user)
        except ResourceAlreadyExists:
            exc_raised = True
        assert exc_raised

    @staticmethod
    @pytest.mark.asyncio
    async def test_delete_success(single_user, memory_store):
        await memory_store.create(single_user)
        assert single_user.get("id") in memory_store.resource_db
        user_id = single_user.get("id")
        await memory_store.delete(user_id)
        user_deleted = False
        try:
            await memory_store.get_by_id(user_id)
        except ResourceNotFound:
            user_deleted = True
        assert user_deleted

    @staticmethod
    @pytest.mark.asyncio
    async def test_delete_nonexistent_resource_fails(single_user, memory_store):
        exc_thrown = False
        try:
            await memory_store.delete("12345")
        except ResourceNotFound:
            exc_thrown = True
        assert exc_thrown

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_by_id_success(single_user, memory_store):
        await memory_store.create(single_user)
        user_id = single_user.get("id")
        actual_user = await memory_store.get_by_id(user_id)
        expected_username = single_user.get("username")
        assert expected_username == actual_user.get("username")
        assert not actual_user.get("password")

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(memory_store):
        user_id = "i.dont.exist@company.com"
        raised = False
        try:
            _ = await memory_store.get_by_id(user_id)
        except ResourceNotFound:
            raised = True
        assert raised

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_success(single_user, memory_store):
        await memory_store.create(single_user)
        user_id = single_user.get("id")
        actual_user = await memory_store.get_by_id(user_id)
        expected_username = single_user.get("username")
        assert expected_username == actual_user.get("username")
        assert not actual_user.get("password")

    @staticmethod
    @pytest.mark.asyncio
    async def test_search_success(users, memory_store):
        # Create a bunch of users in the store:
        _ = await asyncio.gather(*[memory_store.create(u) for u in users])
        random_user: Dict = random.choice(list(memory_store.resource_db.values()))
        email_parts = random_user.get("userName").split("@")
        email_prefix = email_parts[0]
        domain = email_parts[1]
        res, _ = await memory_store.search(f"userName co \"{domain}\"")
        expected_result_size = len(users)
        actual_result_size = len(res)
        assert expected_result_size == actual_result_size

        res, _ = await memory_store.search(f"userName sw \"{email_prefix}\"")
        actual_result_size = len(res)
        assert 1 == actual_result_size

    @staticmethod
    @pytest.mark.asyncio
    async def test_search_pagination_success(users, memory_store):
        _ = await asyncio.gather(*[memory_store.create(u) for u in users])
        first_user: Dict = list(memory_store.resource_db.values())[0]
        fourth_user: Dict = list(memory_store.resource_db.values())[3]
        email_parts = first_user.get("userName").split("@")
        domain = email_parts[1]

        res, _ = await memory_store.search(f"userName co \"{domain}\"", 1, 4)
        expected_result_size = 4
        actual_result_size = len(res)
        assert expected_result_size == actual_result_size

        email_parts = fourth_user.get("userName").split("@")
        email_prefix = email_parts[0]
        res, _ = await memory_store.search(f"userName co \"{domain}\"", 4, 1)
        actual_result_size = len(res)
        assert 1 == actual_result_size
        assert res[0].get("userName").startswith(email_prefix)

        res, _ = await memory_store.search(f"userName co \"{domain}\"", 40, 5)
        actual_result_size = len(res)
        assert 0 == actual_result_size

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_equal_filter(memory_store):
        operation = await memory_store.parse_filter_expression("userName Eq \"john.doe@company.com\"")
        expr = operation.get("expr")
        func = expr.get("func")
        pred = expr.get("pred")
        assert func("john.doe@company.com", pred)
        assert not func("jane.doe@company.com", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_not_equal_filter(memory_store):
        operation = await memory_store.parse_filter_expression("userName Ne \"john.doe@company.com\"")
        expr = operation.get("expr")
        func = expr.get("func")
        pred = expr.get("pred")
        assert func("jane.doe@company.com", pred)
        assert not func("John.Doe@Company.com", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_contains_filter(memory_store):
        operation = await memory_store.parse_filter_expression("userName cO \"john.doe\"")
        expr = operation.get("expr")
        func = expr.get("func")
        pred = expr.get("pred")
        assert func("john.doe@company.com", pred)
        assert not func("microsoft.com", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_starts_with_filter(memory_store):
        operation = await memory_store.parse_filter_expression("userName Sw \"john.doe\"")
        expr = operation.get("expr")
        func = expr.get("func")
        pred = expr.get("pred")
        assert func("John.Doe@Company.com", pred)
        assert not func("Company.com", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_ends_with_filter(memory_store):
        operation = await memory_store.parse_filter_expression("userName ew \"microsoft.com\"")
        expr = operation.get("expr")
        func = expr.get("func")
        pred = expr.get("pred")
        assert func("John.Doe@Microsoft.com", pred)
        assert not func("company.com", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_greater_than_filter(memory_store):
        operation = await memory_store.parse_filter_expression("userName gt \"b\"")
        expr = operation.get("expr")
        func = expr.get("func")
        pred = expr.get("pred")
        assert func("c", pred)
        assert not func("b", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_greater_than_or_equal_to_filter(memory_store):
        operation = await memory_store.parse_filter_expression("userName ge \"b\"")
        expr = operation.get("expr")
        func = expr.get("func")
        pred = expr.get("pred")
        assert func("c", pred)
        assert func("b", pred)
        assert not func("a", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_lower_than_filter(memory_store):
        operation = await memory_store.parse_filter_expression("userName lt \"c\"")
        expr = operation.get("expr")
        func = expr.get("func")
        pred = expr.get("pred")
        assert func("b", pred)
        assert not func("c", pred)
        assert not func("d", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_lower_than_or_equal_to_filter(memory_store):
        operation = await memory_store.parse_filter_expression("userName le \"c\"")
        expr = operation.get("expr")
        func = expr.get("func")
        pred = expr.get("pred")
        assert func("b", pred)
        assert func("c", pred)
        assert not func("d", pred)

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_invalid_operator(memory_store):
        exc_thrown = False
        try:
            _ = await memory_store.parse_filter_expression("userName equals \"c\"")
        except SCIMParserError:
            exc_thrown = True
        assert exc_thrown

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_invalid_operation(memory_store):
        exc_thrown = False
        try:
            _ = await memory_store.parse_filter_expression("userName \"c\" eq")
        except SCIMParserError:
            exc_thrown = True
        assert exc_thrown

    @staticmethod
    @pytest.mark.asyncio
    async def test_parse_complex_expression(memory_store):
        exp_s = "name.familyName Eq \"john.doe@company.com\" AND (something Co \"doe\" OR anotherThing sw \"john\")"
        exp = await memory_store.parse_filter_expression(exp_s)
        assert True

    @staticmethod
    @pytest.mark.asyncio
    async def test_evaluate_full_expression(memory_store, single_user):
        family_name = single_user.get("name").get("familyName")
        given_name = single_user.get("name").get("givenName")
        ci_user = await CaseInsensitiveDict.build_deep(single_user)
        found = await memory_store.evaluate_filter(
            await memory_store.parse_filter_expression(
                f"NAME.familyNamE Eq \"{family_name}\""
            ),
            ci_user
        )
        assert found
        found = await memory_store.evaluate_filter(
            await memory_store.parse_filter_expression(
                f"name.familyName Eq \"{given_name}\""
            ),
            ci_user
        )
        assert not found

    @staticmethod
    @pytest.mark.asyncio
    async def test_evaluate_expression_with_array_lookup(memory_store, single_user):
        ci_user = await CaseInsensitiveDict.build_deep(single_user)
        email = single_user.get("userName")
        found = await memory_store.evaluate_filter(
            await memory_store.parse_filter_expression(
                f"emails Co \"{email}\""
            ),
            ci_user
        )
        assert found

    @staticmethod
    @pytest.mark.asyncio
    async def test_evaluate_expression_with_array_lookup_and_deep_attribute(memory_store, single_user):
        ci_user = await CaseInsensitiveDict.build_deep(single_user)
        email = single_user.get("userName")
        found = await memory_store.evaluate_filter(
            await memory_store.parse_filter_expression(
                f"emails.value eq \"{email}\""
            ),
            ci_user
        )
        assert found

    @staticmethod
    @pytest.mark.asyncio
    async def test_evaluate_expression_with_array_lookup_and_namespace(memory_store, single_user):
        ci_user = await CaseInsensitiveDict.build_deep(single_user)
        email = single_user.get("userName")
        found = await memory_store.evaluate_filter(
            await memory_store.parse_filter_expression(
                f"emails[value eq \"{email}\"]"
            ),
            ci_user
        )
        assert found

    @staticmethod
    @pytest.mark.asyncio
    async def test_evaluate_expression_with_and_logical_expression(memory_store, single_user):
        ci_user = await CaseInsensitiveDict.build_deep(single_user)
        locale_lang = single_user.get("locale").split("-")[0]
        email = single_user.get("userName")
        found = await memory_store.evaluate_filter(
            await memory_store.parse_filter_expression(
                f"userName Eq \"{email}\" and locale Sw \"{locale_lang}-\""
            ),
            ci_user
        )
        assert found

    @staticmethod
    @pytest.mark.asyncio
    async def test_evaluate_expression_with_or_logical_expression(memory_store, single_user):
        ci_user = await CaseInsensitiveDict.build_deep(single_user)
        locale_lang = single_user.get("locale").split("-")[0]
        email = single_user.get("userName")
        found = await memory_store.evaluate_filter(
            await memory_store.parse_filter_expression(
                f"userName Eq \"{email}\" or locale Eq \"he-IL\""
            ),
            ci_user
        )
        assert found

    @staticmethod
    @pytest.mark.asyncio
    async def test_full_search(memory_store, users):
        del users[0]["locale"]
        _ = await asyncio.gather(*[memory_store.create(u) for u in users])
        email_to_search = users[0].get("userName")
        res, _ = await memory_store.search(f"USERNAME sw \"{email_to_search}\"")
        assert len(res) == 1
        res, _ = await memory_store.search(f"locale pr", 1, 3)
        assert len(res) == 3
        res, _ = await memory_store.search(f"USERNAME sw \"{email_to_search}\" and locale pr")
        assert len(res) == 0
