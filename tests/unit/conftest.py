import random
import uuid

import names
import pytest
from aiohttp import web

from scim_2_api.store.memory_store import MemoryStore
from scim_2_api.util.config import Config
from scim_2_api.util.store_util import init_stores


def generate_random_user():
    first_name = names.get_first_name()
    last_name = names.get_last_name()
    email = f"{first_name[0].lower()}{last_name.lower()}@company.com"
    return {
        "emails": [
            {
                "value": email,
                "type": "true",
                "primary": True
            }
        ],
        "externalId": str(uuid.uuid4()),
        "locale": "en-US",
        "name": {
            "formatted": f"{first_name} {last_name}",
            "familyName": last_name,
            "givenName": first_name
        },
        "groups": [
            {}
        ],
        "password": str(uuid.uuid4()),
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User"
        ],
        "id": str(uuid.uuid4()),
        "userName": email,
        "active": True,
        "displayName": f"{first_name} {last_name}"
    }


@pytest.fixture
def users(n: int = 5):
    return [generate_random_user() for _ in range(n)]


@pytest.fixture
def groups():
    return [
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Research & Development",
            "members": []
        },
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Customer Success",
            "members": []
        },
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Finance",
            "members": []
        },
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Human Resources",
            "members": []
        },
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Information Technology",
            "members": []
        }
    ]


@pytest.fixture
def single_group(groups):
    return random.choice(groups)


@pytest.fixture
def single_user(users):
    return random.choice(users)


@pytest.fixture
def memory_store():
    store = MemoryStore()
    yield store
    store.resource_db = {}


@pytest.fixture
def scim_api(aiohttp_client, event_loop, cfg):
    from scim_2_api.rest import get_error_handling_mw
    from scim_2_api.rest.group import get_group_routes
    from scim_2_api.rest.user import get_user_routes
    scim_api = web.Application()
    scim_api.add_routes(get_user_routes(MemoryStore("User")))
    scim_api.add_routes(get_group_routes(MemoryStore(
        "Group",
        name_uniqueness=True,
        resources=None,
        nested_store_attr="members"
    )))
    app = web.Application()
    app.add_subapp("/scim", scim_api)
    ehmw = event_loop.run_until_complete(get_error_handling_mw())
    app.middlewares.append(ehmw)
    return event_loop.run_until_complete(aiohttp_client(app))


@pytest.fixture
def cfg():
    config = Config()
    init_stores()
    return config


@pytest.fixture
def headers(cfg):
    auth_s = cfg.get("authentication.secret")
    return {"Authorization": f"Bearer {auth_s}"}
