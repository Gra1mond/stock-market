import random
import typing

from app.game.models import Move, Player, PlayerStock, Stock
from app.game.states import FinishReason, GameState

if typing.TYPE_CHECKING:
    from app.web.app import Application
    from app.game.accessor import GameAccessor


def calculate_new_price(current_price: int, moves: list[Move], total_players: int) -> int:
    buy_count = sum(1 for m in moves if m.move_type == "buy")
    sell_count = sum(1 for m in moves if m.move_type == "sell")

    net = buy_count - sell_count
    player_impact = net / total_players

    noise = random.uniform(-0.02, 0.02)

    change = player_impact * 0.15 + noise
    change = max(-0.20, min(0.20, change))

    return max(1, round(current_price * (1 + change)))


def get_player_total_value(player: Player, portfolio: list[PlayerStock], stocks: dict[int, Stock]) -> int:
    portfolio_value = sum(
        ps.quantity * stocks[ps.stock_id].current_price
        for ps in portfolio
        if ps.stock_id in stocks
    )
    return player.balance + portfolio_value


async def process_round(
    app: "Application", game_id: int, round_id: int, max_rounds: int
) -> tuple[bool, FinishReason | None, "Player | None"]:
    accessor: "GameAccessor" = app.store.game

    closed = await accessor.try_close_round(round_id)
    if not closed:
        return False, None, None

    players = await accessor.get_players_by_game(game_id)
    moves = await accessor.get_moves_by_round(round_id)
    stocks = await accessor.get_stocks_by_game(game_id)

    for stock in stocks:
        stock_moves = [m for m in moves if m.stock_ticket == stock.ticket_name]
        new_price = calculate_new_price(stock.current_price, stock_moves, len(players))
        await accessor.update_stock_price(stock.id, new_price)

    for move in moves:
        stock = next((s for s in stocks if s.ticket_name == move.stock_ticket), None)
        if not stock:
            continue
        cost = stock.current_price * move.quantity
        if move.move_type == "buy":
            await accessor.update_player_balance(move.player_id, -cost)
            await accessor.upsert_player_stock(move.player_id, stock.id, move.quantity)
        elif move.move_type == "sell":
            await accessor.update_player_balance(move.player_id, cost)
            await accessor.upsert_player_stock(move.player_id, stock.id, -move.quantity)

    if len(players) < 2:
        winner = await finish_game(app, game_id, FinishReason.NOT_ENOUGH_PLAYERS)
        return True, FinishReason.NOT_ENOUGH_PLAYERS, winner

    current_round = await accessor.get_current_round(game_id)
    if current_round and current_round.round_number >= max_rounds:
        winner = await finish_game(app, game_id, FinishReason.ROUNDS_COMPLETED)
        return True, FinishReason.ROUNDS_COMPLETED, winner

    next_number = (current_round.round_number + 1) if current_round else 1
    await accessor.create_round(game_id, next_number)
    return False, None, None


async def finish_game(app: "Application", game_id: int, reason: FinishReason) -> Player | None:
    accessor: "GameAccessor" = app.store.game

    await accessor.update_game_state(GameState.FINISHED, game_id)

    if reason == FinishReason.NOT_ENOUGH_PLAYERS:
        return None

    players = await accessor.get_players_by_game(game_id)
    if not players:
        return None

    stocks_list = await accessor.get_stocks_by_game(game_id)
    stocks = {s.id: s for s in stocks_list}

    scores = []
    for p in players:
        portfolio = await accessor.get_player_portfolio(p.id)
        scores.append((p, get_player_total_value(p, portfolio, stocks)))

    winner = max(scores, key=lambda x: x[1])[0]
    return winner