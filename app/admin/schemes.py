from marshmallow import Schema, fields


class AdminSchema(Schema):
    id = fields.Int(required=False)
    tg_user_id = fields.Int(required=True)
    email = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
