from aiohttp_catcher import Catcher, canned, catch
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from azure_ad_scim_2_api.models import DEFAULT_ERROR_SCHEMA
from azure_ad_scim_2_api.util.exc import ResourceNotFound, ResourceAlreadyExists, UnauthorizedRequest


async def get_error_handling_mw():
    catcher = Catcher(code="status", envelope="detail")
    err_schemas = {"schemas": [DEFAULT_ERROR_SCHEMA]}
    await catcher.add_scenarios(*[sc.with_additional_fields(err_schemas) for sc in canned.AIOHTTP_SCENARIOS])
    await catcher.add_scenarios(
        catch(ResourceNotFound).with_status_code(404).and_stringify().with_additional_fields(err_schemas),
        catch(CosmosResourceNotFoundError).with_status_code(404).and_return(
            "Resource not found").with_additional_fields(err_schemas),
        catch(ResourceAlreadyExists).with_status_code(409).and_stringify().with_additional_fields(err_schemas),
        catch(UnauthorizedRequest).with_status_code(401).and_return("Unauthorized request").with_additional_fields(
            err_schemas)
    )
    return catcher.middleware
