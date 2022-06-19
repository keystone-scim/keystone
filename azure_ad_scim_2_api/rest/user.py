from typing import Dict
import logging

from aiohttp import web
from aiohttp_apispec import (
    docs,
    request_schema,
    response_schema,
    querystring_schema,
)

from azure_ad_scim_2_api.models import ListQueryParams, ErrorResponse
from azure_ad_scim_2_api.models.user import User, ListUsersResponse
from azure_ad_scim_2_api.util.store_util import Stores

LOGGER = logging.getLogger(__name__)
user_routes = web.RouteTableDef()

# user_store = get_user_store()
user_store = Stores().get("users")

@user_routes.view("/Users/{user_id}")
class UserView(web.View):

    @docs(
        tags=["Users"],
        summary="Get a user",
        description="Returns a specific user by ID",
        responses={
            200: {"description": "User search results", "schema": User},
            404: {"description": "User not found", "schema": ErrorResponse}
        },
    )
    async def get(self) -> web.Response:
        user_id = self.request.match_info["user_id"]
        user = await user_store.get_by_id(resource_id=user_id)
        return web.json_response(user)

    @docs(
        tags=["Users"],
        summary="Delete a user",
        description="Deletes a specific user by ID",
        responses={
            200: {"description": "User deleted/deactivated successfully"},
            404: {"description": "User not found", "schema": ErrorResponse}
        },
    )
    async def delete(self) -> web.Response:
        user_id = self.request.match_info["user_id"]
        _ = await user_store.delete(user_id)
        return web.json_response({})

    @docs(
        tags=["Users"],
        summary="Patch a user",
        description="Patch a specific user by ID (partial update)",
        responses={
            200: {"description": "User patched successfully", "schema": User},
            404: {"description": "User not found", "schema": ErrorResponse}
        },
    )
    @request_schema(User(), strict=False)
    async def patch(self) -> web.Response:
        user_id = self.request.match_info["user_id"]
        data: Dict = await self.request.json()
        user = await user_store.update(resource_id=user_id, **data)
        return web.json_response(user)

    @docs(
        tags=["Users"],
        summary="Update a user",
        description="Update a specific user by ID",
        responses={
            200: {"description": "User updated successfully", "schema": User},
            404: {"description": "User not found", "schema": ErrorResponse}
        },
    )
    @request_schema(User(), strict=False)
    async def put(self) -> web.Response:
        user_id = self.request.match_info["user_id"]
        data: Dict = await self.request.json()
        user = await user_store.update(resource_id=user_id, **data)
        return web.json_response(user)


@user_routes.view("/Users")
class UsersView(web.View):

    @docs(
        tags=["Users"],
        summary="Query users",
        description="Perform an administrative search for users with pagination",
        responses={
            200: {"description": "User search results", "schema": ListUsersResponse},
        },
    )
    @request_schema(User, strict=True)
    @querystring_schema(ListQueryParams)
    async def get(self) -> web.Response:
        pass

    @docs(
        tags=["Users"],
        summary="Create a user",
        description="Provision a new user in the tenant",
        responses={
            201: {"description": "User created successfully", "schema": User},
            409: {"description": "User already exists", "schema": ErrorResponse},
        },
    )
    @request_schema(User(), strict=True)
    async def post(self) -> web.Response:
        user: Dict = await self.request.json()
        new_user = await user_store.create(user)
        return web.json_response(new_user, status=201)
