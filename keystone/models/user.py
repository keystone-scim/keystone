from marshmallow import fields, Schema

from keystone.models import BaseResource, ListResponse
from keystone.models.group import Group

DEFAULT_USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"


class Name(Schema):
    formatted = fields.Str()
    family_name = fields.Str(attribute="familyName")
    given_name = fields.Str(attribute="givenName")


class Email(Schema):
    primary = fields.Bool(dump_default=True)
    value = fields.Str(required=True)
    type = fields.Str(dump_default="work")


class User(BaseResource):
    username = fields.Str(attribute="userName")
    id = fields.Str(attribute="id")
    external_id = fields.Str(attribute="externalId")
    schemas = fields.List(fields.Str, dump_default=[DEFAULT_USER_SCHEMA])
    name = fields.Nested(Name)
    display_name = fields.Str(attribute="displayName")
    locale = fields.Str(dump_default="en-US")
    emails = fields.List(fields.Nested(Email))
    groups = fields.List(fields.Nested(Group))
    active = fields.Bool(dump_default=True)
    password = fields.Str()


class ListUsersResponse(ListResponse):
    resources = fields.List(
        fields.Nested(User),
        attribute="Resources",
        dump_default=[]
    )
