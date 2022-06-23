#!/usr/bin/env python3
import logging
import os

from azure_ad_scim_2_api.util.logger import get_log_handler

# Initialize logger prior to loading any other modules:

logger = logging.getLogger()
if int(os.environ.get("JSON_LOGS", "1")) == 1:
    logger.propagate = True
    logger.handlers = [get_log_handler()]


# Initialize config and store singletons:
from azure_ad_scim_2_api.util.config import Config
from azure_ad_scim_2_api.util.store_util import init_stores
CONFIG = Config()
init_stores()

import asyncio
from aiohttp import web
from aiohttp_apispec import AiohttpApiSpec
from aiohttp_catcher import catch, Catcher, canned

from azure_ad_scim_2_api import VERSION
from azure_ad_scim_2_api.rest.user import user_routes
from azure_ad_scim_2_api.rest.group import group_routes
from azure_ad_scim_2_api.models import DEFAULT_ERROR_SCHEMA
from azure_ad_scim_2_api.security.az_keyvault_client import bearer_token_check
from azure_ad_scim_2_api.util.exc import ResourceNotFound, ResourceAlreadyExists, UnauthorizedRequest


async def health(_: web.Request):
    return web.json_response({"healthy": True})


async def serve(host: str = "0.0.0.0", port: int = 5001):
    catcher = Catcher(code="status", envelope="detail")
    err_schemas = {"schemas": [DEFAULT_ERROR_SCHEMA]}
    await catcher.add_scenarios(*[sc.with_additional_fields(err_schemas) for sc in canned.AIOHTTP_SCENARIOS])
    await catcher.add_scenarios(
        catch(ResourceNotFound).with_status_code(404).and_stringify().with_additional_fields(err_schemas),
        catch(ResourceAlreadyExists).with_status_code(409).and_stringify().with_additional_fields(err_schemas),
        catch(UnauthorizedRequest).with_status_code(401).and_return("Unauthorized request").with_additional_fields(err_schemas)
    )

    # Create a sub-app for the SCIM 2.0 API to handle authentication separately from docs:
    scim_api = web.Application()
    scim_api.middlewares.append(catcher.middleware)
    scim_api.middlewares.append(bearer_token_check)
    scim_api.add_routes(user_routes)
    scim_api.add_routes(group_routes)

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
