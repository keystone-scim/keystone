import uuid
from random import choice

import asyncio
import pytest
from psycopg2.errors import UniqueViolation
from pymongo.errors import DuplicateKeyError

from keystone.util.exc import ResourceNotFound


class TestMongoDbStore:

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_user_by_id_fails_for_nonexistent_user(mongodb_stores, rand_id):
        user_store, _ = mongodb_stores
        exc_thrown = False
        try:
            _ = await user_store.get_by_id(rand_id)
        except ResourceNotFound:
            exc_thrown = True
        assert exc_thrown

    @staticmethod
    @pytest.mark.asyncio
    async def test_delete_user_by_id_fails_for_nonexistent_user(mongodb_stores, rand_id):
        user_store, _ = mongodb_stores
        exc_thrown = False
        try:
            _ = await user_store.delete(rand_id)
        except ResourceNotFound:
            exc_thrown = True
        assert exc_thrown

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_user_success(mongodb_stores, single_user):
        user_store, _ = mongodb_stores
        returned_user = await user_store.create(single_user)
        user_id = returned_user.get("id")
        looked_up_user = await user_store.get_by_id(user_id)
        assert looked_up_user.get("id") == user_id
        assert looked_up_user.get("userName") == returned_user.get("userName")

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_user_fails_on_duplicate_username(mongodb_stores, single_user):
        user_store, _ = mongodb_stores
        _ = await user_store.create(single_user)
        duplicate_user = {**single_user}
        del duplicate_user["id"]
        exc_thrown = False
        try:
            _ = await user_store.create(duplicate_user)
        except DuplicateKeyError:
            exc_thrown = True
        assert exc_thrown

    @staticmethod
    @pytest.mark.asyncio
    async def test_delete_user_success(mongodb_stores, single_user):
        user_store, _ = mongodb_stores
        user = await user_store.create(single_user)
        user_id = user.get("id")
        _ = await user_store.delete(user_id)
        exc_thrown = False
        try:
            _ = await user_store.get_by_id(user_id)
        except ResourceNotFound:
            exc_thrown = True
        assert exc_thrown

    @staticmethod
    @pytest.mark.asyncio
    async def test_search_user_by_username(mongodb_stores, single_user):
        user_store, _ = mongodb_stores
        username = single_user.get("userName")
        _ = await user_store.create(single_user)
        _filter = f"userName Eq \"{username}\""
        res, count = await user_store.search(_filter)
        assert 1 == count == len(res)
        assert res[0].get("userName") == username

        mixed_case_username = "".join(choice((str.upper, str.lower))(c) for c in username)
        _filter = f"userName Eq \"{mixed_case_username}\""
        res, count = await user_store.search(_filter)
        assert 1 == count == len(res)
        assert res[0].get("userName") == username

    @staticmethod
    @pytest.mark.asyncio
    async def test_search_user_by_id(mongodb_stores, single_user):
        user_store, _ = mongodb_stores
        user = await user_store.create(single_user)
        user_id = user.get("id")
        _filter = f"id Eq \"{user_id}\""
        res, count = await user_store.search(_filter)
        assert 1 == count == len(res)
        assert res[0].get("userName") == single_user.get("userName")

    @staticmethod
    @pytest.mark.asyncio
    async def test_search_user_by_email(mongodb_stores, single_user):
        user_store, _ = mongodb_stores
        email = single_user.get("userName")
        _ = await user_store.create(single_user)
        _filter = f"emails.value Eq \"{email}\""
        res, count = await user_store.search(_filter)
        assert 1 == count == len(res)
        assert res[0].get("userName") == single_user.get("userName")

        _filter = f"emails Co \"{email}\""
        res, count = await user_store.search(_filter)
        assert 1 == count == len(res)
        assert res[0].get("userName") == single_user.get("userName")

        email_username = email.split("@")[0]
        _filter = f"emails.value Sw \"{email_username}\""
        res, count = await user_store.search(_filter)
        assert 1 == count == len(res)
        assert res[0].get("userName") == single_user.get("userName")

    @staticmethod
    @pytest.mark.asyncio
    async def test_search_user_pagination(mongodb_stores, users):
        user_store, _ = mongodb_stores
        _ = await asyncio.gather(*[user_store.create(u) for u in users])
        email = users[0].get("userName")
        email_domain = email.split("@")[1]
        _filter = f"emails.value co \"{email_domain}\""
        res, count = await user_store.search(_filter, start_index=1, count=3)
        assert len(users) == count
        assert 3 == len(res)

        res, count = await user_store.search(_filter, start_index=4, count=3)
        assert len(users) == count
        assert 2 == len(res)

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_user_success(mongodb_stores, single_user):
        user_store, _ = mongodb_stores
        res = await user_store.create(single_user)
        user_id = res.get("id")
        update_attr = {
            "groups": [],  # To be ignored
            "id": user_id,  # To be ignored
            "invalidAttribute": "foo",  # To be ignored
            "name": {
                "formatted": "John Doe",
                "givenName": "Doe",
                "familyName": "John"
            },
            "locale": "pt-BR",
            "displayName": "John Doe",
            "emails": single_user.get("emails") + [{
                "value": "johndoe@emailprovider.com",
                "primary": False,
                "type": "home"
            }],
        }
        updated_user = await user_store.update(user_id, **update_attr)
        assert "pt-BR" == updated_user.get("locale")
        assert 2 == len(updated_user.get("emails"))
        assert "John Doe" == updated_user.get("displayName") == updated_user.get("name").get("formatted")

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_group_success(mongodb_stores, single_group):
        _, group_store = mongodb_stores
        res = await group_store.create(single_group)
        group_id = res.get("id")

        group = await group_store.get_by_id(group_id)

        assert single_group.get("displayName") == group.get("displayName")

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_group_with_members_success(mongodb_stores, single_group, users):
        user_store, group_store = mongodb_stores
        user_res = await asyncio.gather(*[user_store.create(u) for u in users])
        group_payload = {**single_group, "members": [{
            "value": u.get("id"),
            "display": u.get("userName"),
        } for u in user_res]}
        res = await group_store.create(group_payload)
        group_id = res.get("id")
        group = await group_store.get_by_id(group_id)
        assert len(users) == len(group.get("members"))

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_group_by_id_fails_for_nonexistent_group(mongodb_stores, rand_id):
        _, group_store = mongodb_stores
        exc_thrown = False
        try:
            _ = await group_store.get_by_id(rand_id)
        except ResourceNotFound:
            exc_thrown = True
        assert exc_thrown

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_group_metadata_success(mongodb_stores, single_group):
        _, group_store = mongodb_stores
        res = await group_store.create(single_group)
        group_id = res.get("id")
        update_attr = {
            "id": group_id,  # To be ignored
            "displayName": "New Group Name"
        }
        group = await group_store.update(group_id, **update_attr)
        assert "New Group Name" == group.get("displayName")

    @staticmethod
    @pytest.mark.asyncio
    async def test_delete_group_success(mongodb_stores, single_group):
        _, group_store = mongodb_stores
        group = await group_store.create(single_group)
        group_id = group.get("id")
        _ = await group_store.delete(group_id)
        exc_thrown = False
        try:
            _ = await group_store.get_by_id(group_id)
        except ResourceNotFound:
            exc_thrown = True
        assert exc_thrown

    @staticmethod
    @pytest.mark.asyncio
    async def test_delete_group_fails_for_nonexistent_group(mongodb_stores, rand_id):
        _, group_store = mongodb_stores
        exc_thrown = False
        try:
            _ = await group_store.delete(rand_id)
        except ResourceNotFound:
            exc_thrown = True
        assert exc_thrown

    @staticmethod
    @pytest.mark.asyncio
    async def test_add_users_to_group(mongodb_stores, single_group, users):
        user_store, group_store = mongodb_stores
        _ = await asyncio.gather(*[user_store.create(u) for u in users])
        ret_users, _ = await user_store.search()
        res = await group_store.create(single_group)
        group_id = res.get("id")
        _ = await asyncio.gather(*[group_store.add_user_to_group(u.get("id"), group_id) for u in ret_users])
        group = await group_store.get_by_id(group_id)
        assert len(users) == len(group.get("members"))

    @staticmethod
    @pytest.mark.asyncio
    async def test_remove_users_from_group(mongodb_stores, single_group, users):
        user_store, group_store = mongodb_stores
        _ = await asyncio.gather(*[user_store.create(u) for u in users])
        ret_users, _ = await user_store.search()
        res = await group_store.create(single_group)
        group_id = res.get("id")
        _ = await asyncio.gather(*[group_store.add_user_to_group(
            user_id=u.get("id"),
            group_id=group_id
        ) for u in ret_users])
        group = await group_store.get_by_id(group_id)
        assert len(users) == len(group.get("members"))

        _ = await group_store.remove_users_from_group(
            user_ids=[u.get("id") for u in ret_users],
            group_id=group_id
        )
        group = await group_store.get_by_id(group_id)
        assert 0 == len(group.get("members"))

    @staticmethod
    @pytest.mark.asyncio
    async def test_set_group_members(mongodb_stores, single_group, users):
        user_store, group_store = mongodb_stores
        uc_res = await asyncio.gather(*[user_store.create(u) for u in users])
        cohort_1 = uc_res[:2]
        cohort_2 = uc_res[2:len(uc_res)]
        res = await group_store.create(single_group)
        group_id = res.get("id")
        _ = await asyncio.gather(*[group_store.add_user_to_group(u.get("id"), group_id) for u in cohort_1])
        group = await group_store.get_by_id(group_id)
        assert 2 == len(group.get("members"))
        _ = await group_store.set_group_members(
            user_ids=[u.get("id") for u in cohort_2],
            group_id=group_id
        )
        group = await group_store.get_by_id(group_id)
        assert len(users) - 2 == len(group.get("members"))

    @staticmethod
    @pytest.mark.asyncio
    async def test_search_groups(mongodb_stores, groups):
        _, group_store = mongodb_stores
        _ = await asyncio.gather(*[group_store.create(g) for g in groups])
        _filter = f"displayName Eq \"Human Resources\""
        res, count = await group_store.search(_filter)
        assert 1 == count
        assert "Human Resources" == res[0].get("displayName")

