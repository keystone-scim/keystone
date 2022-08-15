#!/usr/bin/env python3
import logging
import os

from keystone import VERSION, LOGO, InterceptHandler
from keystone.store.postgresql_store import set_up_schema
from keystone.util.logger import get_log_handler

# Initialize logger prior to loading any other modules:

if int(os.environ.get("JSON_LOGS", "0")) == 1:
    logger = logging.getLogger()
    logger.propagate = True
    logger.handlers = [get_log_handler()]
else:
    logger = logging.getLogger()
    logger.propagate = True
    logger.handlers = [InterceptHandler()]

# Initialize config and store singletons:
from keystone.util.config import Config
from keystone.util.store_util import init_stores
CONFIG = Config()
stores = init_stores()

import asyncio
from aiohttp import web
from aiohttp_apispec import AiohttpApiSpec

from keystone.rest import get_error_handling_mw
from keystone.rest.user import get_user_routes
from keystone.rest.group import get_group_routes
from keystone.security.authn import bearer_token_check


async def health(_: web.Request):
    return web.json_response({"healthy": True})


async def root(_: web.Request):
    return web.HTTPFound("/api/docs")


async def print_logo(_logger):
    return [_logger.info(f" {ln}") for ln in LOGO.split("\n")]


async def serve(host: str = "0.0.0.0", port: int = 5001):
    if CONFIG.get("store.type") == "PostgreSQL":
        set_up_schema()

    error_handling_mw = await get_error_handling_mw()

    # Create a sub-app for the SCIM 2.0 API to handle authentication separately from docs:
    scim_api = web.Application()
    scim_api.middlewares.append(error_handling_mw)
    scim_api.middlewares.append(bearer_token_check)
    scim_api.add_routes(get_user_routes())
    scim_api.add_routes(get_group_routes())

    # Append SCIM 2.0 API to root web app:
    app = web.Application()
    app.add_subapp("/scim", scim_api)
    # Register OpenAPI docs (swagger):
    _ = AiohttpApiSpec(
        app=app,
        title="SCIM 2.0 API Documentation",
        version="v1",
        url="/api/docs/swagger.json",
        swagger_path="/api/docs"
    )
    # Health/readiness probe endpoint:
    app.add_routes([web.get("/", root)])
    app.add_routes([web.get("/health", health)])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await print_logo(logger)
    logger.info(
        "Keystone server listening on http://%s:%d, log level: %s", host, port, os.getenv("LOG_LEVEL", "INFO").upper()
    )
    await site.start()


def run() -> None:
    loop = asyncio.get_event_loop()
    try:
        logger.info("Running version %s of the API", VERSION)
        loop.run_until_complete(serve())
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("User-initiated termination")
    except Exception as e:
        logger.exception("An error has occurred")
        exit(9)
    finally:
        loop.close()
        exit(0)


if __name__ == "__main__":
    run()
