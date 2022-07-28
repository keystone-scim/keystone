#!/usr/bin/env python3
import logging
import os

from scim_2_api.util.logger import get_log_handler

# Initialize logger prior to loading any other modules:

logger = logging.getLogger()
if int(os.environ.get("JSON_LOGS", "1")) == 1:
    logger.propagate = True
    logger.handlers = [get_log_handler()]


# Initialize config and store singletons:
from scim_2_api.util.config import Config
from scim_2_api.util.store_util import init_stores
CONFIG = Config()
init_stores()

import asyncio
from aiohttp import web
from aiohttp_apispec import AiohttpApiSpec

from scim_2_api import VERSION
from scim_2_api.rest import get_error_handling_mw
from scim_2_api.rest.user import get_user_routes
from scim_2_api.rest.group import get_group_routes
from scim_2_api.security.az_keyvault_client import bearer_token_check


async def health(_: web.Request):
    return web.json_response({"healthy": True})


async def root(_: web.Request):
    return web.HTTPFound("/api/docs")


async def serve(host: str = "0.0.0.0", port: int = 5001):
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
    logger.info(
        "API server listening on http://%s:%d, log level: %s", host, port, os.getenv("LOG_LEVEL", "INFO").upper()
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
