from urllib.parse import quote
import asyncio
import random

import pytest


class TestGroupRest:

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_group_success(scim_api, single_group, headers):
        resp = await scim_api.post("/scim/Groups", json=single_group, headers=headers)
        assert resp.status == 201
        assert single_group["displayName"] == (await resp.json())["displayName"]

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_duplicate_group_fails(scim_api, single_group, headers):
        resp = await scim_api.post("/scim/Groups", json=single_group, headers=headers)
        assert resp.status == 201
        resp = await scim_api.post("/scim/Groups", json=single_group, headers=headers)
        assert resp.status == 409

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_group_by_id_success(scim_api, single_group, headers):
        resp = await scim_api.post("/scim/Groups", json=single_group, headers=headers)
        assert resp.status == 201
        group_id = (await resp.json()).get("id")
        resp = await scim_api.get(f"/scim/Groups/{group_id}", headers=headers)
        assert resp.status == 200

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_nonexistent_group_by_id_fails(scim_api, headers):
        group_id = "does_not_exist"
        resp = await scim_api.get(f"/scim/Groups/{group_id}", headers=headers)
        assert resp.status == 404

    @staticmethod
    @pytest.mark.asyncio
    async def test_delete_group_success(scim_api, single_group, headers):
        resp = await scim_api.post("/scim/Groups", json=single_group, headers=headers)
        assert resp.status == 201
        group_id = (await resp.json()).get("id")
        resp = await scim_api.get(f"/scim/Groups/{group_id}", headers=headers)
        assert resp.status == 200
        resp = await scim_api.delete(f"/scim/Groups/{group_id}", headers=headers)
        assert resp.status == 200
        resp = await scim_api.get(f"/scim/Groups/{group_id}", headers=headers)
        assert resp.status == 404

    @staticmethod
    @pytest.mark.asyncio
    async def test_delete_nonexistent_group_fails(scim_api, headers):
        group_id = "does_not_exist"
        resp = await scim_api.get(f"/scim/Groups/{group_id}", headers=headers)
        assert resp.status == 404

    @staticmethod
    @pytest.mark.asyncio
    async def test_patch_group_by_adding_users(scim_api, single_group, users, headers):
        resp = await scim_api.post("/scim/Groups", json=single_group, headers=headers)
        assert resp.status == 201
        group_id = (await resp.json()).get("id")
        patch_payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{
                "op": "add",
                "path": "members",
                "value": [{
                    "value": u["id"],
                    "display": u["userName"],
                } for u in users]
            }]
        }
        resp = await scim_api.patch(f"/scim/Groups/{group_id}", json=patch_payload, headers=headers)
        assert resp.status == 200

        resp = await scim_api.get(f"/scim/Groups/{group_id}", headers=headers)
        assert len(users) == len((await resp.json())["members"])

    @staticmethod
    @pytest.mark.asyncio
    async def test_patch_group_by_replacing_members(scim_api, single_group, users, headers):
        resp = await scim_api.post("/scim/Groups", json=single_group, headers=headers)
        assert resp.status == 201

        first_user = users[0]
        remaining_users = users[1:len(users)]
        assert resp.status == 201
        group_id = (await resp.json()).get("id")
        patch_payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{
                "op": "add",
                "path": "members",
                "value": [{
                    "value": first_user["id"],
                    "display": first_user["userName"],
                }]
            }]
        }
        resp = await scim_api.patch(f"/scim/Groups/{group_id}", json=patch_payload, headers=headers)
        assert resp.status == 200

        patch_payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{
                "op": "replace",
                "path": "members",
                "value": [{
                    "value": u["id"],
                    "display": u["userName"],
                } for u in remaining_users]
            }]
        }
        resp = await scim_api.patch(f"/scim/Groups/{group_id}", json=patch_payload, headers=headers)
        assert resp.status == 200

        resp = await scim_api.get(f"/scim/Groups/{group_id}", headers=headers)
        assert len(remaining_users) == len((await resp.json())["members"])

    @staticmethod
    @pytest.mark.asyncio
    async def test_patch_group_by_removing_users(scim_api, single_group, users, headers):
        resp = await scim_api.post("/scim/Groups", json=single_group, headers=headers)
        assert resp.status == 201
        group_id = (await resp.json()).get("id")
        patch_payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{
                "op": "add",
                "path": "members",
                "value": [{
                    "value": u["id"],
                    "display": u["userName"],
                } for u in users]
            }]
        }
        resp = await scim_api.patch(f"/scim/Groups/{group_id}", json=patch_payload, headers=headers)
        assert resp.status == 200
        removed_user = users[0]
        patch_payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{
                "op": "remove",
                "path": "members",
                "value": [{
                    "value": removed_user["id"],
                    "display": removed_user["userName"],
                }]
            }]
        }
        resp = await scim_api.patch(f"/scim/Groups/{group_id}", json=patch_payload, headers=headers)
        assert resp.status == 200
        resp = await scim_api.get(f"/scim/Groups/{group_id}", headers=headers)
        remaining_users = (await resp.json())["members"]
        assert len(users) - 1 == len(remaining_users)
        assert removed_user["id"] not in [u["value"] for u in remaining_users]

    @staticmethod
    @pytest.mark.asyncio
    async def test_patch_group_by_removing_user_with_path(scim_api, single_group, users, headers):
        resp = await scim_api.post("/scim/Groups", json=single_group, headers=headers)
        assert resp.status == 201
        group_id = (await resp.json()).get("id")
        patch_payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{
                "op": "add",
                "path": "members",
                "value": [{
                    "value": u["id"],
                    "display": u["userName"],
                } for u in users]
            }]
        }
        resp = await scim_api.patch(f"/scim/Groups/{group_id}", json=patch_payload, headers=headers)
        assert resp.status == 200
        removed_user = users[0]
        patch_payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{
                "op": "remove",
                "path": f"members[value eq \"{removed_user['id']}\"]",
            }]
        }
        resp = await scim_api.patch(f"/scim/Groups/{group_id}", json=patch_payload, headers=headers)
        assert resp.status == 200
        resp = await scim_api.get(f"/scim/Groups/{group_id}", headers=headers)
        remaining_users = (await resp.json())["members"]
        assert len(users) - 1 == len(remaining_users)
        assert removed_user["id"] not in [u["value"] for u in remaining_users]

    @staticmethod
    @pytest.mark.asyncio
    async def test_patch_group_data(scim_api, single_group, headers):
        resp = await scim_api.post("/scim/Groups", json=single_group, headers=headers)
        assert resp.status == 201
        group_id = (await resp.json()).get("id")
        group_name = (await resp.json()).get("displayName")
        patch_payload = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{
                "op": "replace",
                "value": {
                    "displayName": group_name[::-1]
                }
            }]
        }
        resp = await scim_api.patch(f"/scim/Groups/{group_id}", json=patch_payload, headers=headers)
        assert resp.status == 200
        assert group_name[::-1] == (await resp.json()).get("displayName")

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_groups(scim_api, groups, headers):
        responses = await asyncio.gather(*[
            scim_api.post("/scim/Groups", json=g, headers=headers)
            for g in groups
        ])
        assert 201 * len(groups) == sum([r.status for r in responses])
        random_group = random.choice(groups)
        group_name = quote(random_group.get("displayName"))
        fltr = f"displayName eq \"{group_name}\""
        search_url = f"/scim/Groups?filter={fltr}&count=1"
        resp = await scim_api.get(search_url, headers=headers)
        assert resp.status == 200
        assert len((await resp.json())["Resources"]) == 1
