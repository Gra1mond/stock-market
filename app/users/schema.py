from marshmallow import Schema, fields


class UserLoginSchema(Schema):
    username = fields.Str(required=True)


class UserResponseSchema(Schema):
    id = fields.Str(required=True)
    username = fields.Str(required=True)
    is_admin = fields.Bool(required=True)
