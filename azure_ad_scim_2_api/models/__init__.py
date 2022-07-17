from marshmallow import fields, Schema


DEFAULT_LIST_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
DEFAULT_ERROR_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:Error"
DEFAULT_PATCH_OP_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:PatchOp"


class BaseResource(Schema):
    pass


class ListQueryParams(Schema):
    start_index = fields.Str(attribute="startIndex", dump_default="1")
    count = fields.Str(attribute="count", dump_default="100")
    filter = fields.Str()


class ListResponse(Schema):
    schemas = fields.List(fields.Str, dump_default=[DEFAULT_LIST_SCHEMA])
    total_results = fields.Int(attribute="totalResults", required=True)
    start_index = fields.Int(attribute="startIndex", required=True)
    items_per_page = fields.Int(attribute="itemsPerPage", required=True)
    resources = fields.List(
        fields.Nested(BaseResource),
        attribute="Resources",
        dump_default=[]
    )


class ErrorResponse(Schema):
    schemas = fields.List(fields.Str, dump_default=[DEFAULT_ERROR_SCHEMA])
    detail = fields.Str(required=True)
    status = fields.Int(required=True)


class AuthHeaders(Schema):
    authorization = fields.Str(attribute="Authorization", required=True)


__all__ = [
    "AuthHeaders",
    "BaseResource",
    "ErrorResponse",
    "ListQueryParams",
    "ListResponse",
    "DEFAULT_ERROR_SCHEMA",
    "DEFAULT_LIST_SCHEMA",
    "DEFAULT_PATCH_OP_SCHEMA",
]
