import asyncio
import typing

from app.bot.keyboards import command_keyboard
from app.bot.manager import start_round
from app.game.accessor import GameAccessor
from app.game.logic import finish_game
from app.game.models import Player, Round, Stock
from app.game.states import FinishReason, GameState
from app.store.bot.accessor import BotAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application

MAX_ROUNDS = 10
ROUND_DURATION = 60
STARTING_BALANCE = 1000


COMMAND_LABELS = {
    "новая игра": "/new_game",
    "старт": "/start",
    "присоединиться": "/join",
    "готов": "/ready",
    "завершить игру": "/end_game",
}


class MoveContext(typing.NamedTuple):
    player: Player
    current_round: Round
    stock: Stock


class GameHandler:
    def __init__(self, app: "Application"):
        self.app = app
        self._round_task: asyncio.Task | None = None

    @property
    def accessor(self) -> GameAccessor:
        return self.app.store.game

    @property
    def bot(self) -> BotAccessor:
        return self.app.store.bot

    async def handle_new_game(self, chat_id: int) -> None:
        existing = await self.accessor.get_game_by_chat_id(chat_id)
        if existing and existing.state != GameState.FINISHED:
            await self.bot.send_message(
                chat_id, "Игра уже запущена в этом чате."
            )
            return
        await self.accessor.create_game(chat_id)
        await self.bot.send_message(
            chat_id,
            (
                "Игра создана! Используйте /join чтобы вступить, "
                "/start чтобы начать."
            ),
        )

    async def handle_join(
        self, chat_id: int, tg_user_id: int, username: str | None
    ) -> None:
        game = await self.accessor.get_game_by_chat_id(chat_id)
        if not game or game.state != GameState.WAITING:
            await self.bot.send_message(
                chat_id, "Нет активной игры. Используйте /new_game."
            )
            return
        existing_player = await self.accessor.get_player(tg_user_id, game.id)
        if existing_player:
            await self.bot.send_message(chat_id, "Вы уже в игре.")
            return
        await self.accessor.create_player(
            tg_user_id, game.id, username=username
        )
        display_name = f"@{username}" if username else str(tg_user_id)
        await self.bot.send_message(
            chat_id, f"Игрок {display_name} вступил в игру!"
        )

    async def handle_start(self, chat_id: int) -> None:
        game = await self.accessor.get_game_by_chat_id(chat_id)
        if not game or game.state != GameState.WAITING:
            await self.bot.send_message(chat_id, "Нет игры в ожидании.")
            return
        players = await self.accessor.get_players_by_game(game.id)
        if len(players) < 2:
            await self.bot.send_message(chat_id, "Нужно минимум 2 игрока.")
            return
        await self.accessor.create_stock(game.id, "SBER", 100)
        await self.accessor.create_stock(game.id, "GAZP", 80)
        await self.accessor.create_stock(game.id, "YNDX", 120)
        await self.accessor.update_game_state(GameState.IN_PROGRESS, game.id)
        await self.accessor.create_round(
            game.id, round_number=1, duration_seconds=ROUND_DURATION
        )
        players = await self.accessor.get_players_by_game(game_id=game.id)
        await self.bot.send_message(
            chat_id,
            (
                "Игра началась!\n"
                f"Стартовый баланс всех пользователей {STARTING_BALANCE}₽"
            ),
        )
        participants = []
        for player in players:
            display = (
                f"@{player.tg_username}"
                if player.tg_username
                else str(player.tg_user_id)
            )
            participants.append(f"• {display}")
        await self.bot.send_message(
            chat_id, "Участники:\n" + "\n".join(participants)
        )
        self._round_task = asyncio.create_task(
            start_round(self.app, game.id, chat_id, MAX_ROUNDS, ROUND_DURATION)
        )

    async def handle_buy(
        self, chat_id: int, tg_user_id: int, ticket: str, quantity: int
    ) -> None:
        await self._handle_move(chat_id, tg_user_id, "buy", ticket, quantity)

    async def handle_sell(
        self, chat_id: int, tg_user_id: int, ticket: str, quantity: int
    ) -> None:
        await self._handle_move(chat_id, tg_user_id, "sell", ticket, quantity)

    async def _prepare_move(
        self,
        chat_id: int,
        tg_user_id: int,
        ticket: str,
        quantity: int,
    ) -> tuple[MoveContext | None, str | None]:
        game = await self.accessor.get_game_by_chat_id(chat_id)
        error_message: str | None = None
        player: Player | None = None
        current_round: Round | None = None
        stock: Stock | None = None
        if not game or game.state != GameState.IN_PROGRESS:
            error_message = "Игра не идёт."
        else:
            player = await self.accessor.get_player(tg_user_id, game.id)
            if not player:
                error_message = "Вы не в игре."
            elif player.balance < 0:
                error_message = (
                    "Баланс отрицательный, вы банкрот — "
                    "игра для вас окончена."
                )
            else:
                current_round = await self.accessor.get_current_round(game.id)
                if not current_round:
                    error_message = "Раунд не найден."
                else:
                    stock = await self.accessor.get_stock_by_ticket(
                        game.id, ticket
                    )
                    if not stock:
                        error_message = f"Акция {ticket} " "не найдена."
                    elif quantity <= 0:
                        error_message = "Количество должно быть положительным."
        if error_message or not (player and current_round and stock):
            return None, error_message
        return MoveContext(player, current_round, stock), None

    async def _handle_move(
        self,
        chat_id: int,
        tg_user_id: int,
        move_type: str,
        ticket: str,
        quantity: int,
    ) -> None:
        context, error = await self._prepare_move(
            chat_id, tg_user_id, ticket, quantity
        )
        if error:
            await self.bot.send_message(chat_id, error)
            return
        assert context is not None
        player = context.player
        current_round = context.current_round
        stock = context.stock
        cost = stock.current_price * quantity
        error_message: str | None = None
        new_balance = player.balance
        if move_type == "sell":
            all_stock = await self.accessor.get_player_portfolio(
                player_id=player.id
            )
            stock_entry = next(
                (ps for ps in all_stock if ps.stock_id == stock.id), None
            )
            if not stock_entry or stock_entry.quantity < quantity:
                error_message = (
                    "У вас недостаточно акций " "в портфеле для продажи."
                )
            else:
                await self.accessor.update_player_balance(
                    player_id=player.id, delta=cost
                )
                await self.accessor.upsert_player_stock(
                    player_id=player.id,
                    stock_id=stock.id,
                    quantity_delta=-quantity,
                )
                new_balance = player.balance + cost
        elif move_type == "buy":
            if player.balance < cost:
                error_message = "Недостаточно средств для покупки."
            else:
                await self.accessor.update_player_balance(player.id, -cost)
                await self.accessor.upsert_player_stock(
                    player.id,
                    stock.id,
                    quantity,
                )
                new_balance = player.balance - cost
        else:
            error_message = "Неизвестный тип действия."
        if error_message:
            await self.bot.send_message(chat_id, error_message)
            return
        await self.accessor.create_move(
            current_round.id, move_type, player.id, ticket, quantity
        )
        message = f"Ход принят: {move_type.upper()} {ticket} x{quantity}"
        if move_type == "buy":
            message += f" — баланс: {new_balance}₽"
        await self.bot.send_message(chat_id, message)

    def _extract_command_and_args(
        self, text: str
    ) -> tuple[str | None, list[str]]:
        stripped = text.strip()
        if not stripped:
            return None, []
        tokens = stripped.split()
        for idx, token in enumerate(tokens):
            if token.startswith("/"):
                command = token.split("@", 1)[0].lower()
                return command, tokens[idx + 1 :]
        lower = stripped.lower()
        return COMMAND_LABELS.get(lower), []

    async def handle(
        self, chat_id: int, tg_user_id: int, username: str | None, text: str
    ) -> None:
        command, args = self._extract_command_and_args(text)
        if command:
            handled = await self._dispatch_command(
                command, args, chat_id, tg_user_id, username
            )
            if handled:
                return
        quick_command, quick_ticker, quick_qty = self._parse_quick_order(text)
        if quick_command and quick_ticker and quick_qty is not None:
            if quick_command == "/buy":
                await self.handle_buy(
                    chat_id, tg_user_id, quick_ticker, quick_qty
                )
            else:
                await self.handle_sell(
                    chat_id, tg_user_id, quick_ticker, quick_qty
                )
            return
        if text:
            await self.bot.send_message(chat_id, text)

    async def _dispatch_command(
        self,
        command: str,
        args: list[str],
        chat_id: int,
        tg_user_id: int,
        username: str | None,
    ) -> bool:
        simple_handlers: dict[
            str,
            typing.Callable[[], typing.Coroutine[typing.Any, typing.Any, None]],
        ] = {
            "/new_game": lambda: self.handle_new_game(chat_id),
            "/join": lambda: self.handle_join(chat_id, tg_user_id, username),
            "/start": lambda: self.handle_start(chat_id),
            "/ready": lambda: self.handle_ready(chat_id, tg_user_id),
            "/end_game": lambda: self.handle_end_game(chat_id, tg_user_id),
        }
        handler = simple_handlers.get(command)
        if handler:
            await handler()
            return True
        if command in ("/buy", "/sell"):
            if len(args) < 2:
                await self.bot.send_message(
                    chat_id, "Укажите тикер и количество."
                )
                return True
            ticket = args[0].upper()
            try:
                quantity = int(args[1])
            except ValueError:
                await self.bot.send_message(
                    chat_id, "Количество должно быть целым числом."
                )
                return True
            if command == "/buy":
                await self.handle_buy(chat_id, tg_user_id, ticket, quantity)
            else:
                await self.handle_sell(chat_id, tg_user_id, ticket, quantity)
            return True
        return False

    def _parse_quick_order(
        self, text: str
    ) -> tuple[str | None, str | None, int | None]:
        lower = text.strip().lower()
        for action in ("купить", "продать"):
            if lower.startswith(action):
                parts = lower.split()
                if len(parts) >= 3:
                    ticker = parts[1].upper()
                    qty_part = parts[-1]
                    if qty_part.startswith("x"):
                        qty_text = qty_part[1:]
                    else:
                        qty_text = qty_part
                    try:
                        qty = int(qty_text)
                    except ValueError:
                        return None, None, None
                    command = "/buy" if action == "купить" else "/sell"
                    return command, ticker, qty
        return None, None, None

    async def handle_end_game(self, chat_id: int, tg_user_id: int) -> None:
        game = await self.accessor.get_game_by_chat_id(chat_id)
        if not game or game.state != GameState.IN_PROGRESS:
            await self.bot.send_message(chat_id, "Нет активной игры.")
            return
        player = await self.accessor.get_player(tg_user_id, game.id)
        if not player:
            await self.bot.send_message(chat_id, "Вы не в игре.")
            return
        current_round = await self.accessor.get_current_round(game.id)
        if current_round:
            await self.accessor.try_close_round(current_round.id)
        winners, capital = await finish_game(
            self.app, game.id, FinishReason.FORCED_BY_PLAYER
        )
        if winners:
            names = []
            for winner in winners:
                display = (
                    f"@{winner.tg_username}"
                    if winner.tg_username
                    else str(winner.tg_user_id)
                )
                names.append(display)
            await self.bot.send_message(
                chat_id,
                (
                    "Игра остановлена. Победитель(и): "
                    f"{', '.join(names)}! \n с капиталом {capital}"
                ),
                reply_markup=command_keyboard(),
            )
        else:
            await self.bot.send_message(
                chat_id, "Игра остановлена.", reply_markup=command_keyboard()
            )

    async def handle_ready(self, chat_id: int, tg_user_id: int) -> None:
        error_message: str | None = None
        game = await self.accessor.get_game_by_chat_id(chat_id)
        player: Player | None = None
        current_round: Round | None = None
        if not game or game.state != GameState.IN_PROGRESS:
            error_message = "Игра не идёт."
        else:
            player = await self.accessor.get_player(tg_user_id, game.id)
            if not player:
                error_message = "Вы не в игре."
            else:
                current_round = await self.accessor.get_current_round(game.id)
                if not current_round:
                    error_message = "Раунд не найден."
        if error_message or not (player and current_round):
            await self.bot.send_message(
                chat_id, error_message or "Неизвестная ошибка."
            )
            return

        status, ready_count, expected_count = (
            self.accessor.mark_player_ready_for_round(
                current_round.id, player.id
            )
        )

        status_messages = {
            "not_managed": "Раунд ещё не начался или уже завершён.",
            "not_expected": "Вы не участвуете в текущем раунде.",
            "already_ready": "Вы уже подтвердили завершение хода.",
        }
        if status in status_messages:
            await self.bot.send_message(chat_id, status_messages[status])
            return
        if expected_count == 0:
            await self.bot.send_message(
                chat_id, "Нет активных игроков в этом раунде."
            )
            return
        if status == "completed":
            await self.bot.send_message(
                chat_id, "Все игроки подтвердили окончание хода."
            )
            return

        remaining = expected_count - ready_count
        await self.bot.send_message(
            chat_id,
            f"Ход принят, ждём ещё {remaining} игрока(ов) до завершения.",
        )
