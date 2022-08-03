#!/usr/bin/env python3

import asyncio

from scim_2_api.util.config import Config
from scim_2_api.util.store_util import Stores, init_stores

CONFIG = Config()


async def clean_up():
    user_store = Stores().get("users")
    # group_store = Stores().get("groups")
    print("Cleaning up stores")
    _ = await asyncio.gather(user_store.clean_up_store())
    print("Clean-up done")


if __name__ == "__main__":
    init_stores()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(clean_up())
    exit(0)
