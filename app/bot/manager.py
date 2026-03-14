import asyncio
import typing

from app.game.accessor import GameAccessor
from app.game.logic import process_round
from app.game.states import FinishReason, GameState
from app.store.bot.accessor import BotAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application


async def start_round(
    app: "Application",
    game_id: int,
    chat_id: int,
    max_rounds: int,
    duration: int = 60,
) -> None:
    accessor: GameAccessor = app.store.game
    bot: BotAccessor = app.store.bot

    new_round = await accessor.get_current_round(game_id)
    if not new_round:
        return
    stocks = await accessor.get_stocks_by_game(game_id)
    prices_text = "\n".join(f"{s.ticket_name}: {s.current_price}₽" for s in stocks)
    await bot.send_message(
        chat_id,
        f"Раунд {new_round.round_number} начался! У вас {duration} секунд.\nРаундов до конца: {max_rounds-new_round.round_number}\n\n{prices_text}\n\nИспользуйте /buy и /sell",
    )

    game = await accessor.get_game(game_id)
    if not game or game.state != GameState.IN_PROGRESS:
        return

    await asyncio.sleep(duration)

    game = await accessor.get_game(game_id)
    if not game or game.state != GameState.IN_PROGRESS:
        return
    is_finished, reason, winners, _ = await process_round(app, game_id, new_round.id, max_rounds)

    if is_finished:
        await announce_winner(app, chat_id, winners, reason)
        return

    await announce_round_results(app, chat_id, game_id)

    next_round = await accessor.get_current_round(game_id)
    if next_round:
        await start_round(app, game_id, chat_id, max_rounds, duration)


async def announce_round_results(app: "Application", chat_id: int, game_id: int) -> None:
    bot: BotAccessor = app.store.bot
    accessor: GameAccessor = app.store.game

    stocks = await accessor.get_stocks_by_game(game_id)
    prices_text = "\n".join(f"{s.ticket_name}: {s.current_price}₽" for s in stocks)
    await bot.send_message(chat_id, f"Итоги раунда:\n\n{prices_text}")


async def announce_winner(app: "Application", chat_id: int, winners: list, reason: FinishReason) -> None:
    bot: BotAccessor = app.store.bot

    if reason == FinishReason.NOT_ENOUGH_PLAYERS:
        text = "Игра завершена: недостаточно игроков."
    elif winners:
        winner_names = []
        for winner in winners:
            name = f"@{winner.tg_username}" if winner.tg_username else str(winner.tg_user_id)
            winner_names.append(name)
        text = f"Игра завершена! Победитель(и): {', '.join(winner_names)} с итоговым капиталом {winners[0].balance}."
    else:
        text = "Игра завершена!"

    await bot.send_message(chat_id, text)
