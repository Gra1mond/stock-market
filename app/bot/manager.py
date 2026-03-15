import asyncio
import typing
from contextlib import suppress

from app.bot.keyboards import command_keyboard, quick_order_keyboard
from app.game.accessor import GameAccessor
from app.game.logic import collect_solvent_players, process_round
from app.game.models import Stock
from app.game.states import FinishReason, GameState
from app.store.bot.accessor import BotAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application


def format_stock_prices(stocks: list[Stock]) -> str:
    return "\n".join(
        f"{stock.ticket_name}: {stock.current_price}₽" for stock in stocks
    )


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
    await bot.send_message(
        chat_id,
        (
            f"Раунд {new_round.round_number} начался! У вас "
            f"{duration} секунд.\n"
            f"Раундов до конца: {max_rounds - new_round.round_number}\n\n"
            f"{format_stock_prices(stocks)}\n\n"
            "Используйте /buy, /sell и /ready — завершающий ход когда готовы."
        ),
        reply_markup=command_keyboard(),
    )

    solvent_players, _ = await collect_solvent_players(
        accessor,
        await accessor.get_players_by_game(game_id),
        stocks,
    )
    ready_event = accessor.init_round_completion(
        new_round.id, [player.id for player in solvent_players]
    )

    game = await accessor.get_game(game_id)
    if not game or game.state != GameState.IN_PROGRESS:
        return

    stock_names = [s.ticket_name for s in stocks]
    if stock_names:
        await bot.send_message(
            chat_id,
            (
                "Быстрые кнопки для покупок/продаж "
                "по фиксированным количествам."
            ),
            reply_markup=quick_order_keyboard(stock_names),
        )
        await bot.send_message(
            chat_id,
            (
                "Чтобы выбрать другое количество, просто напишите "
                "`/buy ТИКЕР КОЛИЧЕСТВО` вручную."
            ),
        )

    wait_ready = asyncio.create_task(ready_event.wait())
    wait_timeout = asyncio.create_task(asyncio.sleep(duration))
    pending: set[asyncio.Task] = set()
    try:
        await asyncio.wait(
            {wait_ready, wait_timeout}, return_when=asyncio.FIRST_COMPLETED
        )
    finally:
        for task in pending:
            task.cancel()
        for task in pending:
            with suppress(asyncio.CancelledError):
                await task
        accessor.cleanup_round_completion(new_round.id)

    if ready_event.is_set() and solvent_players:
        await bot.send_message(
            chat_id,
            "Все игроки подтвердили конец хода, завершаем текущий раунд.",
        )

    game = await accessor.get_game(game_id)
    if not game or game.state != GameState.IN_PROGRESS:
        return
    is_finished, reason, winners, _ = await process_round(
        app, game_id, new_round.id, max_rounds
    )

    if is_finished:
        await announce_winner(app, chat_id, winners, reason)
        return

    await announce_round_results(app, chat_id, game_id)

    if await accessor.get_current_round(game_id):
        await start_round(app, game_id, chat_id, max_rounds, duration)


async def announce_round_results(
    app: "Application", chat_id: int, game_id: int
) -> None:
    bot: BotAccessor = app.store.bot
    accessor: GameAccessor = app.store.game

    stocks = await accessor.get_stocks_by_game(game_id)
    await bot.send_message(
        chat_id,
        f"Итоги раунда:\n\n{format_stock_prices(stocks)}",
        reply_markup=command_keyboard(),
    )


async def announce_winner(
    app: "Application", chat_id: int, winners: list, reason: FinishReason
) -> None:
    bot: BotAccessor = app.store.bot

    if reason == FinishReason.NOT_ENOUGH_PLAYERS:
        text = "Игра завершена: недостаточно игроков."
    elif winners:
        winner_names = []
        for winner in winners:
            name = (
                f"@{winner.tg_username}"
                if winner.tg_username
                else str(winner.tg_user_id)
            )
            winner_names.append(name)
        text = (
            "Игра завершена! Победитель(и): "
            f"{', '.join(winner_names)} "
            f"с итоговым капиталом {winners[0].balance}."
        )
    else:
        text = "Игра завершена!"

    await bot.send_message(chat_id, text, reply_markup=command_keyboard())
