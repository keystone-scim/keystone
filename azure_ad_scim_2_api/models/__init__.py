from marshmallow import fields, Schema


DEFAULT_LIST_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
DEFAULT_ERROR_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:Error"
DEFAULT_PATCH_OP_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:PatchOp"


class BaseResource(Schema):
    pass


class ListQueryParams(Schema):
    start_index = fields.Str(attribute="startIndex", default="1")
    count = fields.Str(attribute="itemsPerPage", default="100")
    filter = fields.Str()


class ListResponse(Schema):
    schemas = fields.List(fields.Str, default=[DEFAULT_LIST_SCHEMA])
    total_results = fields.Int(attribute="totalResults", required=True)
    start_index = fields.Int(attribute="startIndex", required=True)
    items_per_page = fields.Int(attribute="itemsPerPage", required=True)
    resources = fields.List(
        fields.Nested(BaseResource),
        attribute="Resources",
        default=[]
    )


class ErrorResponse(Schema):
    schemas = fields.List(fields.Str, default=[DEFAULT_ERROR_SCHEMA])
    detail = fields.Str(required=True)
    status = fields.Int(required=True)


__all__ = [
    "BaseResource",
    "ErrorResponse",
    "ListQueryParams",
    "ListResponse",
    "DEFAULT_PATCH_OP_SCHEMA",
]
