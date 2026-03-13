import asyncio
import typing

from app.bot.manager import start_round
from app.game.accessor import GameAccessor
from app.game.logic import finish_game
from app.game.states import FinishReason, GameState
from app.store.bot.accessor import BotAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application

MAX_ROUNDS = 10
ROUND_DURATION = 60
STARTING_BALANCE = 1000


class GameHandler:
    def __init__(self, app: "Application"):
        self.app = app

    @property
    def accessor(self) -> GameAccessor:
        return self.app.store.game

    @property
    def bot(self) -> BotAccessor:
        return self.app.store.bot

    async def handle_new_game(self, chat_id: int) -> None:
        existing = await self.accessor.get_game_by_chat_id(chat_id)
        if existing and existing.state != GameState.FINISHED:
            await self.bot.send_message(chat_id, "Игра уже запущена в этом чате.")
            return
        await self.accessor.create_game(chat_id)
        await self.bot.send_message(chat_id, "Игра создана! Используйте /join чтобы вступить, /start чтобы начать.")

    async def handle_join(self, chat_id: int, tg_user_id: int) -> None:
        game = await self.accessor.get_game_by_chat_id(chat_id)
        if not game or game.state != GameState.WAITING:
            await self.bot.send_message(chat_id, "Нет активной игры. Используйте /new_game.")
            return
        existing_player = await self.accessor.get_player(tg_user_id,game.id)
        if existing_player:
            await self.bot.send_message(chat_id, "Вы уже в игре.")
            return
        await self.accessor.create_player(tg_user_id, game.id)
        await self.bot.send_message(chat_id, f"Игрок {tg_user_id} вступил в игру!")

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
        await self.accessor.create_round(game.id, round_number=1, duration_seconds=ROUND_DURATION)
        await self.bot.send_message(chat_id, "Игра началась!")
        asyncio.create_task(start_round(self.app, game.id, chat_id, MAX_ROUNDS, ROUND_DURATION))

    async def handle_buy(self, chat_id: int, tg_user_id: int, ticket: str, quantity: int) -> None:
        await self._handle_move(chat_id, tg_user_id, "buy", ticket, quantity)

    async def handle_sell(self, chat_id: int, tg_user_id: int, ticket: str, quantity: int) -> None:
        await self._handle_move(chat_id, tg_user_id, "sell", ticket, quantity)

    async def _handle_move(self, chat_id: int, tg_user_id: int, move_type: str, ticket: str, quantity: int) -> None:
        game = await self.accessor.get_game_by_chat_id(chat_id)
        if not game or game.state != GameState.IN_PROGRESS:
            await self.bot.send_message(chat_id, "Игра не идёт.")
            return
        player = await self.accessor.get_player(tg_user_id)
        if not player:
            await self.bot.send_message(chat_id, "Вы не в игре.")
            return
        current_round = await self.accessor.get_current_round(game.id)
        if not current_round:
            await self.bot.send_message(chat_id, "Раунд не найден.")
            return
        await self.accessor.create_move(current_round.id, move_type, player.id, ticket, quantity)
        await self.bot.send_message(chat_id, f"Ход принят: {move_type.upper()} {ticket} x{quantity}")

    async def handle(self, chat_id: int, tg_user_id: int, text: str) -> None:
        parts = text.strip().split()
        if not parts:
            return
        command = parts[0].lower()
        if command == "/new_game":
            await self.handle_new_game(chat_id)
        elif command == "/join":
            await self.handle_join(chat_id, tg_user_id)
        elif command == "/start":
            await self.handle_start(chat_id)
        elif command == "/buy" and len(parts) == 3:
            await self.handle_buy(chat_id, tg_user_id, parts[1].upper(), int(parts[2]))
        elif command == "/sell" and len(parts) == 3:
            await self.handle_sell(chat_id, tg_user_id, parts[1].upper(), int(parts[2]))
        elif command == "/end_game":
            await self.handle_end_game(chat_id, tg_user_id)

    async def handle_end_game(self, chat_id: int, tg_user_id: int) -> None:
        game = await self.accessor.get_game_by_chat_id(chat_id)
        if not game or game.state != GameState.IN_PROGRESS:
            await self.bot.send_message(chat_id, "Нет активной игры.")
            return
        player = await self.accessor.get_player(tg_user_id, game.id)
        if not player:
            await self.bot.send_message(chat_id, "Вы не в игре.")
            return
        winner = await finish_game(self.app, game.id, FinishReason.FORCED_BY_PLAYER)
        if winner:
            await self.bot.send_message(chat_id, f"Игра остановлена. Победитель: {winner.tg_user_id}!")
        else:
            await self.bot.send_message(chat_id, "Игра остановлена.")
