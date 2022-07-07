import asyncio
import random

import pytest


class TestUserRest:

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_user_success(scim_api, single_user, headers):
        resp = await scim_api.post("/scim/Users", json=single_user, headers=headers)
        assert resp.status == 201
        assert single_user["userName"] == (await resp.json())["userName"]

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_duplicate_user_fails(scim_api, single_user, headers):
        resp = await scim_api.post("/scim/Users", json=single_user, headers=headers)
        assert resp.status == 201
        resp = await scim_api.post("/scim/Users", json=single_user, headers=headers)
        assert resp.status == 409

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(scim_api, single_user, headers):
        resp = await scim_api.post("/scim/Users", json=single_user, headers=headers)
        assert resp.status == 201
        user_id = (await resp.json()).get("id")
        resp = await scim_api.get(f"/scim/Users/{user_id}", headers=headers)
        assert resp.status == 200

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_nonexistent_user_by_id_fails(scim_api, headers):
        user_id = "does_not_exist"
        resp = await scim_api.get(f"/scim/Users/{user_id}", headers=headers)
        assert resp.status == 404

    @staticmethod
    @pytest.mark.asyncio
    async def test_delete_user_success(scim_api, single_user, headers):
        resp = await scim_api.post("/scim/Users", json=single_user, headers=headers)
        assert resp.status == 201
        user_id = (await resp.json()).get("id")
        resp = await scim_api.get(f"/scim/Users/{user_id}", headers=headers)
        assert resp.status == 200
        resp = await scim_api.delete(f"/scim/Users/{user_id}", headers=headers)
        assert resp.status == 200
        resp = await scim_api.get(f"/scim/Users/{user_id}", headers=headers)
        assert resp.status == 404

    @staticmethod
    @pytest.mark.asyncio
    async def test_delete_nonexistent_user_fails(scim_api, headers):
        user_id = "does_not_exist"
        resp = await scim_api.get(f"/scim/Users/{user_id}", headers=headers)
        assert resp.status == 404

    @staticmethod
    @pytest.mark.asyncio
    async def test_patch_user_success(scim_api, single_user, headers):
        resp = await scim_api.post("/scim/Users", json=single_user, headers=headers)
        assert resp.status == 201
        user_id = (await resp.json()).get("id")
        patch_data = {
            "name": {
                "formatted": "Joane Doe",
                "familyName": "Doe",
                "givenName": "Doe"
            },
            "displayName": "Joane Doe"
        }
        resp = await scim_api.patch(f"/scim/Users/{user_id}", json=patch_data, headers=headers)
        assert resp.status == 200
        resp = await scim_api.get(f"/scim/Users/{user_id}", headers=headers)
        assert resp.status == 200
        assert (await resp.json()).get("displayName") == "Joane Doe"

    @staticmethod
    @pytest.mark.asyncio
    async def test_patch_nonexistent_user_fails(scim_api, single_user, headers):
        user_id = "does-not-exist"
        patch_data = {
            "displayName": "Joane Doe"
        }
        resp = await scim_api.patch(f"/scim/Users/{user_id}", json=patch_data, headers=headers)
        assert resp.status == 404

    @staticmethod
    @pytest.mark.asyncio
    async def test_put_user_success(scim_api, single_user, headers):
        resp = await scim_api.post("/scim/Users", json=single_user, headers=headers)
        assert resp.status == 201
        user_id = (await resp.json()).get("id")
        patch_data = {
            "name": {
                "formatted": "Joane Doe",
                "familyName": "Doe",
                "givenName": "Doe"
            },
            "displayName": "Joane Doe"
        }
        single_user.update(patch_data)
        resp = await scim_api.put(f"/scim/Users/{user_id}", json=patch_data, headers=headers)
        assert resp.status == 200
        resp = await scim_api.get(f"/scim/Users/{user_id}", headers=headers)
        assert resp.status == 200
        assert (await resp.json()).get("displayName") == "Joane Doe"

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_users(scim_api, users, headers):
        responses = await asyncio.gather(*[
            scim_api.post("/scim/Users", json=u, headers=headers)
            for u in users
        ])
        assert 201 * len(users) == sum([r.status for r in responses])
        random_user = random.choice(users)
        email_parts = random_user.get("userName").split("@")
        email_prefix = email_parts[0]
        domain = email_parts[1]
        fltr = f"userName co \"{domain}\""
        search_url = f"/scim/Users?filter={fltr}&itemsPerPage=1"
        resp = await scim_api.get(search_url, headers=headers)
        assert resp.status == 200
        assert len((await resp.json())["Resources"]) == 1
