from typing import Dict
import logging

from aiohttp import web
from aiohttp_apispec import (
    docs,
    request_schema,
    querystring_schema,
)

from azure_ad_scim_2_api.models import ListQueryParams, ErrorResponse
from azure_ad_scim_2_api.models.group import Group, PatchGroupOp, ListGroupsResponse
from azure_ad_scim_2_api.util.store_util import Stores


LOGGER = logging.getLogger(__name__)
group_routes = web.RouteTableDef()

group_store = Stores().get("groups")


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
        group_id = self.request.match_info["group_id"]
        data: Dict = await self.request.json()
        group = await group_store.update(resource_id=group_id, **data)
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
        pass

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
        new_group = await group_store.create(group)
        return web.json_response(new_group, status=201)
