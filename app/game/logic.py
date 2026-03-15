import random
import typing

from app.game.constants import STARTING_BALANCE
from app.game.models import Move, Player, PlayerStock, Stock
from app.game.states import FinishReason, GameState

if typing.TYPE_CHECKING:
    from app.game.accessor import GameAccessor
    from app.web.app import Application


def calculate_new_price(
    current_price: int, moves: list[Move], total_players: int
) -> int:
    buy_count = sum(1 for m in moves if m.move_type == "buy")
    sell_count = sum(1 for m in moves if m.move_type == "sell")

    net = buy_count - sell_count
    player_impact = net / total_players

    noise = random.uniform(-0.02, 0.02)

    change = player_impact * 0.15 + noise
    change = max(-0.20, min(0.20, change))

    return max(1, round(current_price * (1 + change)))


def get_player_total_value(
    player: Player, portfolio: list[PlayerStock], stocks: dict[int, Stock]
) -> int:
    portfolio_value = sum(
        ps.quantity * stocks[ps.stock_id].current_price
        for ps in portfolio
        if ps.stock_id in stocks
    )
    return player.balance + portfolio_value


async def collect_solvent_players(
    accessor: "GameAccessor", players: list[Player], stocks: list[Stock]
) -> tuple[list[Player], dict[int, Stock]]:
    stocks_dict = {s.id: s for s in stocks}
    solvent_players: list[Player] = []
    for player in players:
        portfolio = await accessor.get_player_portfolio(player.id)
        total_value = get_player_total_value(player, portfolio, stocks_dict)
        if total_value > 0:
            solvent_players.append(player)
    return solvent_players, stocks_dict


async def process_round(
    app: "Application", game_id: int, round_id: int, max_rounds: int
) -> tuple[bool, FinishReason | None, list[Player], int]:
    accessor: "GameAccessor" = app.store.game

    current_round = await accessor.get_round(round_id)
    if not current_round:
        return False, None, []

    closed = await accessor.try_close_round(round_id)
    if not closed:
        return False, None, []

    players = await accessor.get_players_by_game(game_id)
    moves = await accessor.get_moves_by_round(round_id)
    stocks = await accessor.get_stocks_by_game(game_id)
    solvent_players, _ = await collect_solvent_players(
        accessor, players, stocks
    )

    for stock in stocks:
        stock_moves = [m for m in moves if m.stock_ticket == stock.ticket_name]
        new_price = calculate_new_price(
            stock.current_price, stock_moves, max(1, len(solvent_players))
        )
        await accessor.update_stock_price(stock.id, new_price)
        stock.current_price = new_price

    if len(solvent_players) < 2:
        winners, total = await finish_game(
            app, game_id, FinishReason.NOT_ENOUGH_PLAYERS
        )
        return True, FinishReason.NOT_ENOUGH_PLAYERS, winners, total

    if current_round.round_number >= max_rounds:
        winners, total = await finish_game(
            app, game_id, FinishReason.ROUNDS_COMPLETED
        )
        return True, FinishReason.ROUNDS_COMPLETED, winners, total

    next_number = current_round.round_number + 1
    await accessor.create_round(game_id, next_number)
    return False, None, [], 0


async def finish_game(
    app: "Application", game_id: int, reason: FinishReason
) -> tuple[list[Player], int]:
    accessor: "GameAccessor" = app.store.game

    if reason == FinishReason.NOT_ENOUGH_PLAYERS:
        await accessor.update_game_state(GameState.FINISHED, game_id)
        await accessor.cleanup_game_resources(game_id)
        return [], 0

    players = await accessor.get_players_by_game(game_id)
    if not players:
        await accessor.update_game_state(GameState.FINISHED, game_id)
        await accessor.cleanup_game_resources(game_id)
        return [], 0

    stocks_list = await accessor.get_stocks_by_game(game_id)
    stocks = {s.id: s for s in stocks_list}

    scores = []
    for p in players:
        portfolio = await accessor.get_player_portfolio(p.id)
        scores.append((p, get_player_total_value(p, portfolio, stocks)))

    for player, score in scores:
        balance_delta = score - STARTING_BALANCE
        await accessor.upsert_leaderboard_entry(
            game_id,
            player.id,
            player.tg_user_id,
            player.tg_username,
            balance_delta,
        )

    max_value = max(score for _, score in scores)
    winners = [player for player, score in scores if score == max_value]
    await accessor.update_game_state(GameState.FINISHED, game_id)
    await accessor.cleanup_game_resources(game_id)
    return winners, max_value
