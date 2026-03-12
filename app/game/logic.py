from app.game.models import Move


def process_round(game_id:int):
    pass

import random

def calculate_new_price(current_price: int, moves: list[Move], total_players: int) -> int:
    buy_count = sum(1 for m in moves if m.move_type == "buy")
    sell_count = sum(1 for m in moves if m.move_type == "sell")

    net = buy_count - sell_count
    player_impact = net / total_players  

    noise = random.uniform(-0.02, 0.02)  

    change = player_impact * 0.15 + noise  
    change = max(-0.20, min(0.20, change))  

    return max(1, round(current_price * (1 + change)))


def finish_game():
    pass