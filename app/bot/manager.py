import asyncio
import typing

from app.game.accessor import GameAccessor
from app.game.logic import process_round
from app.game.states import FinishReason
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
        f"Раунд {new_round.round_number} начался! У вас {duration} секунд.\n\n{prices_text}\n\nИспользуйте /buy и /sell",
    )

    await asyncio.sleep(duration)

    is_finished, reason, winner = await process_round(app, game_id, new_round.id, max_rounds)

    if is_finished:
        await announce_winner(app, chat_id, winner, reason)
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


async def announce_winner(app: "Application", chat_id: int, winner, reason: FinishReason) -> None:
    bot: BotAccessor = app.store.bot

    if reason == FinishReason.NOT_ENOUGH_PLAYERS:
        text = "Игра завершена: недостаточно игроков."
    elif winner:
        text = f"Игра завершена! Победитель: @{winner.tg_user_id} с итоговым капиталом."
    else:
        text = "Игра завершена!"

    await bot.send_message(chat_id, text)
