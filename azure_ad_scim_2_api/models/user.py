from marshmallow import fields, Schema

from azure_ad_scim_2_api.models import BaseResource, ListResponse
from azure_ad_scim_2_api.models.group import Group

DEFAULT_USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"


class Name(Schema):
    formatted = fields.Str()
    family_name = fields.Str(attribute="familyName")
    given_name = fields.Str(attribute="givenName")


class Email(Schema):
    primary = fields.Bool(default=True)
    value = fields.Str(required=True)
    type = fields.Str(default="work")


class User(BaseResource):
    username = fields.Str(attribute="userName")
    id = fields.Str(attribute="id")
    external_id = fields.Str(attribute="externalId")
    schemas = fields.List(fields.Str, default=[DEFAULT_USER_SCHEMA])
    name = fields.Nested(Name)
    display_name = fields.Str(attribute="displayName")
    locale = fields.Str(default="en-US")
    emails = fields.List(fields.Nested(Email))
    groups = fields.List(fields.Nested(Group))
    active = fields.Bool(default=True)
    password = fields.Str()


class ListUsersResponse(ListResponse):
    resources = fields.List(
        fields.Nested(User),
        attribute="Resources",
        default=[]
    )
