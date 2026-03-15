from marshmallow import Schema, fields


class PlayerStockSchema(Schema):
    stock_id = fields.Int(required=True)
    quantity = fields.Int(required=True)


class PlayerSchema(Schema):
    id = fields.Int(required=True)
    tg_user_id = fields.Int(required=True)
    tg_username = fields.Str(allow_none=True)
    balance = fields.Int(required=True)
    stock_portfolio = fields.List(
        fields.Nested(PlayerStockSchema), dump_only=True
    )


class StockSchema(Schema):
    id = fields.Int(required=True)
    game_id = fields.Int(required=True)
    ticket_name = fields.Str(required=True)
    current_price = fields.Int(required=True)


class RoundSchema(Schema):
    id = fields.Int(required=True)
    game_id = fields.Int(required=True)
    round_number = fields.Int(required=True)
    current_status = fields.Str(required=True)
    deadline = fields.DateTime(required=True)


class MoveSchema(Schema):
    id = fields.Int(required=True)
    player_id = fields.Int(required=True)
    round_id = fields.Int(required=True)
    move_type = fields.Str(required=True)
    stock_ticket = fields.Str(required=True)
    quantity = fields.Int(required=True)
