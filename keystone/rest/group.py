from typing import Dict
import logging
import sys

from aiohttp import web
from aiohttp_apispec import (
    docs,
    request_schema,
    querystring_schema,
)

from keystone.models import ListQueryParams, ErrorResponse, DEFAULT_LIST_SCHEMA
from keystone.models.group import Group, PatchGroupOp, ListGroupsResponse
from keystone.store import BaseStore
from keystone.util.store_util import Stores

LOGGER = logging.getLogger(__name__)


def get_group_routes(_group_store: BaseStore = None):
    group_routes = web.RouteTableDef()
    group_store = _group_store or Stores().get("groups")

    @group_routes.view("/Groups/{group_id}")
    class GroupView(web.View):

        @docs(
            tags=["Groups"],
            summary="Get a group",
            description="Returns a specific group by ID",
            responses={
                200: {"description": "Group search results", "schema": Group},
                404: {"description": "Group not found", "schema": ErrorResponse}
            },
        )
        async def get(self) -> web.Response:
            group_id = self.request.match_info["group_id"]
            group = await group_store.get_by_id(resource_id=group_id)
            return web.json_response(group)

        @docs(
            tags=["Groups"],
            summary="Delete a group",
            description="Deletes a specific group by ID",
            responses={
                200: {"description": "Group deleted successfully"},
                404: {"description": "Group not found", "schema": ErrorResponse}
            },
        )
        async def delete(self) -> web.Response:
            group_id = self.request.match_info["group_id"]
            _ = await group_store.delete(group_id)
            return web.json_response({})

        async def _execute_group_operation(self, operation: Dict) -> Dict:
            """
            Scenarios:

            1. Patch group metadata: replace operation without a path.
                {
                    "op": "replace",
                    "value": {
                        "id": "abf4dd94-a4c0-4f67-89c9-76b03340cb9b",
                        "displayName": "Test SCIMv2"
                    }
                }
            2. Add or remove members with a path
                {
                    "op": "{add, remove}",
                    "path": "members[value eq "89bb1940-b905-4575-9e7f-6f887cfb368e"]"
                }
            3. Add or remove a list of members with a "members" path and values list:
                {
                    "op": "{add, remove}",
                    "path": "members",
                    "value": [{
                        "value": "23a35c27-23d3-4c03-b4c5-6443c09e7173",
                        "display": "test.user@company.com"
                    }]
                }
            4. Override the entire list of members with "replace" op and "members" path:
                {
                    "op": "replace",
                    "path": "members",
                    "value": [
                        {
                            "value": "23a35c27-23d3-4c03-b4c5-6443c09e7173",
                            "display": "test.user@okta.local"
                        },
                        {
                            "value": "89bb1940-b905-4575-9e7f-6f887cfb368e",
                            "display": "test.user@okta.local"
                        }
                    ]
                }
            """
            group_id = self.request.match_info["group_id"]
            if hasattr(group_store, "resource_db"):
                group = group_store.resource_db[group_id]
            else:
                group = await group_store.get_by_id(group_id)
            op_type = operation.get("op")
            op_value = operation.get("value")
            op_path = operation.get("path")

            if op_type == "replace" and not op_path:
                # Patch group metadata: replace operation without a path
                return await group_store.update(group_id, **op_value)
            if op_path and op_path.startswith("members[") and not op_value:
                # Remove members with a path:
                selected_members, _ = await group["members_store"].search(
                    _filter=op_path.strip("members[").strip("]"),
                    start_index=1,
                    count=sys.maxsize
                )
                for member in selected_members:
                    if op_type == "remove":
                        await group["members_store"].delete(member.get("value"))
                    return group
            if op_path == "members" and op_type == "replace" and op_value:
                return await group_store.update(group_id, **{"members": op_value})
            if op_path == "members" and op_value:
                for member in op_value:
                    member_id = member.get("value")
                    if op_type == "add":
                        await group["members_store"].create(member)
                    elif op_type == "remove":
                        await group["members_store"].delete(member_id)
                return group

            return {}

        @docs(
            tags=["Groups"],
            summary="Patch a group",
            description="Patch a specific group by ID (partial update)",
            responses={
                200: {"description": "Group patched successfully"},
                404: {"description": "Group not found", "schema": ErrorResponse}
            },
        )
        @request_schema(PatchGroupOp, strict=False)
        async def patch(self) -> web.Response:
            data: Dict = await self.request.json()
            operations = data.get("Operations")
            group = {}
            for operation in operations:
                group = await self._execute_group_operation(operation)
            group = await group_store.get_by_id(group["id"])
            return web.json_response(group)

    @group_routes.view("/Groups")
    class GroupsView(web.View):

        @docs(
            tags=["Groups"],
            summary="Query groups",
            description="Perform an administrative search for groups with pagination",
            responses={
                200: {"description": "Group search results", "schema": ListGroupsResponse},
            },
        )
        @request_schema(Group, strict=True)
        @querystring_schema(ListQueryParams)
        async def get(self) -> web.Response:
            start_index = int(self.request.query.get("startIndex", "1"))
            items_per_page = int(self.request.query.get("count", "100"))
            groups, total_results = await group_store.search(
                _filter=self.request.query.get("filter"),
                start_index=start_index,
                count=items_per_page,
            )
            for g in groups:
                if "member_ids" in g:
                    del g["member_ids"]
            return web.json_response({
                "schemas": [DEFAULT_LIST_SCHEMA],
                "startIndex": start_index,
                "totalResults": total_results,
                "itemsPerPage": items_per_page,
                "Resources": groups,
            })

        @docs(
            tags=["Groups"],
            summary="Create a group",
            description="Provision a new group in the tenant",
            responses={
                201: {"description": "Group created successfully", "schema": Group},
                409: {"description": "Group already exists", "schema": ErrorResponse},
            },
        )
        @request_schema(Group, strict=True)
        async def post(self) -> web.Response:
            group: Dict = await self.request.json()
            group["members"] = group.get("members", [])
            if not group.get("meta"):
                group["meta"] = {"resourceType": "Group"}
            new_group = await group_store.create(group)
            return web.json_response(new_group, status=201)

    return group_routes
