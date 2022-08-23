import random
from typing import Callable

import asyncio
import pytest
from aiohttp import web
from aiohttp.test_utils import BaseTestServer, TestServer, TestClient
from aiohttp.web_app import Application

from keystone_scim.store import postgresql_store
from keystone_scim.store import mongodb_store
from keystone_scim.util.config import Config
from keystone_scim.util.store_util import init_stores


def gen_random_hex(length: int = 24):
    return f"%0{length}x" % random.randrange(16**length)


def build_user(first_name, last_name, guid):
    email = f"{first_name[0].lower()}{last_name.lower()}@company.com"
    return {
        "emails": [
            {
                "value": email,
                "type": "true",
                "primary": True
            }
        ],
        "externalId": guid,
        "locale": "en-US",
        "name": {
            "formatted": f"{first_name} {last_name}",
            "familyName": last_name,
            "givenName": first_name,
        },
        "groups": [
            {}
        ],
        "password": guid,
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User"
        ],
        "id": guid,
        "userName": email,
        "active": True,
        "displayName": f"{first_name} {last_name}"
    }


@pytest.fixture(scope="module")
def initial_user():
    return build_user("Alex", "Smith", "6303270163fc418d32450cd9")


@pytest.fixture(scope="module")
def second_user():
    return build_user("Daniel", "Gonzales", "63033e376d9d20f702bc0a11")


@pytest.fixture(scope="module")
def module_scoped_event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def module_scoped_aiohttp_client(module_scoped_event_loop):
    loop = module_scoped_event_loop
    clients = []

    async def go(__param, *args, server_kwargs=None, **kwargs):

        if isinstance(__param, Callable) and not isinstance(  # type: ignore[arg-type]
            __param, (Application, BaseTestServer)
        ):
            __param = __param(loop, *args, **kwargs)
            kwargs = {}
        else:
            assert not args, "args should be empty"

        if isinstance(__param, Application):
            server_kwargs = server_kwargs or {}
            server = TestServer(__param, loop=loop, **server_kwargs)
            client = TestClient(server, loop=loop, **kwargs)
        elif isinstance(__param, BaseTestServer):
            client = TestClient(__param, loop=loop, **kwargs)
        else:
            raise ValueError("Unknown argument type: %r" % type(__param))

        await client.start_server()
        clients.append(client)
        return client

    yield go

    async def finalize() -> None:
        while clients:
            await clients.pop().close()

    # loop.run_until_complete(finalize())


@pytest.fixture(scope="module")
def scim_api(module_scoped_aiohttp_client, module_scoped_event_loop, cfg, initial_user, headers):
    from keystone_scim.rest import get_error_handling_mw
    from keystone_scim.rest.group import get_group_routes
    from keystone_scim.rest.user import get_user_routes

    scim_api = web.Application()
    scim_api.add_routes(get_user_routes())
    scim_api.add_routes(get_group_routes())
    app = web.Application()
    app.add_subapp("/scim", scim_api)

    app.middlewares.append(
        module_scoped_event_loop.run_until_complete(get_error_handling_mw())
    )
    if cfg.get("store.pg.host") is not None:
        postgresql_store.set_up_schema()
    elif cfg.get("store.mongo.host") or cfg.get("store.mongo.dsn"):
        module_scoped_event_loop.run_until_complete(mongodb_store.set_up())
    c = module_scoped_event_loop.run_until_complete(module_scoped_aiohttp_client(app))
    module_scoped_event_loop.run_until_complete(c.post("/scim/Users", json=initial_user, headers=headers))
    return c


@pytest.fixture(scope="module")
def cfg():
    config = Config()
    init_stores()
    yield config


@pytest.fixture(scope="module")
def headers(cfg):
    auth_s = cfg.get("authentication.secret")
    yield {
        "Authorization": f"Bearer {auth_s}",
        "Accept": "application/scim+json",
    }


@pytest.fixture(scope="module")
def run_async(module_scoped_event_loop):
    def f(async_f):
        return module_scoped_event_loop.run_until_complete(async_f)
    return f


@pytest.fixture(scope="module")
def users_endpoint_response(run_async, scim_api, headers):
    url = "/scim/Users?count=1&startIndex=1"
    return run_async(scim_api.get(url, headers=headers))


@pytest.fixture(scope="module")
def user_by_id_endpoint_response(run_async, scim_api, headers, initial_user):
    url = f"/scim/Users/{initial_user['id']}"
    return run_async(scim_api.get(url, headers=headers))


@pytest.fixture(scope="module")
def invalid_user_by_username_response(run_async, scim_api, headers):
    invalid_username = "does.not.exist.in@organization.org"
    url = f"/scim/Users?filter=userName eq \"{invalid_username}\""
    return run_async(scim_api.get(url, headers=headers))


@pytest.fixture(scope="module")
def invalid_user_by_id_response(run_async, scim_api, headers):
    invalid_user_id = gen_random_hex()  # str(uuid.uuid4())
    url = f"/scim/Users/{invalid_user_id}"
    return run_async(scim_api.get(url, headers=headers))


@pytest.fixture(scope="module")
def random_user_nonexistent_response(run_async, scim_api, headers):
    random_username = f"{gen_random_hex()}@organization.org"
    url = f"/scim/Users?filter=userName eq \"{random_username}\""
    return run_async(scim_api.get(url, headers=headers))


@pytest.fixture(scope="module")
def create_realistic_user_response(run_async, scim_api, headers, second_user):
    url = f"/scim/Users"
    resp = run_async(scim_api.post(url, json=second_user, headers=headers))
    return resp


@pytest.fixture(scope="module")
def verify_user_created_response(run_async, scim_api, headers, second_user):
    url = f"/scim/Users/{second_user['id']}"
    return run_async(scim_api.get(url, headers=headers))


@pytest.fixture(scope="module")
def username_case_sensitivity_response(run_async, scim_api, headers, second_user):
    username = second_user.get("userName").upper()
    url = f"/scim/Users?filter=userName eq \"{username}\""
    return run_async(scim_api.get(url, headers=headers))
