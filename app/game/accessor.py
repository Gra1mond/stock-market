import asyncio
import typing
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select, update

from app.base.base_accessor import BaseAccessor
from app.game.constants import STARTING_BALANCE
from app.game.models import (
    Game,
    LeaderboardEntry,
    Move,
    Player,
    PlayerStock,
    Round,
    Stock,
)
from app.game.states import GameState

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameAccessor(BaseAccessor):
    def __init__(self, app: "Application"):
        super().__init__(app)
        self._round_completion_state: dict[int, dict[str, object]] = {}

    async def create_game(self, chat_id: int) -> Game:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        new_game = Game(chat_id=chat_id, state=GameState.WAITING)
        async with self.app.database.session() as session:
            session.add(new_game)
            await session.commit()
            await session.refresh(new_game)
            return new_game

    async def get_game(self, game_id: int) -> Game | None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            return await session.scalar(select(Game).where(Game.id == game_id))

    async def update_game_state(self, state: str, game_id: int) -> None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            await session.execute(
                update(Game).where(Game.id == game_id).values(state=state)
            )
            await session.commit()

    async def create_player(
        self,
        tg_user_id: int,
        game_id: int,
        balance: int = STARTING_BALANCE,
        username: str | None = None,
    ) -> Player:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        new_player = Player(
            game_id=game_id,
            tg_user_id=tg_user_id,
            balance=balance,
            tg_username=username,
        )
        async with self.app.database.session() as session:
            session.add(new_player)
            await session.commit()
            await session.refresh(new_player)
            return new_player

    async def get_player(
        self, tg_user_id: int, game_id: int | None = None
    ) -> Player | None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            query = select(Player).where(Player.tg_user_id == tg_user_id)
            if game_id is not None:
                query = query.where(Player.game_id == game_id)
            return await session.scalar(query)

    async def get_players_by_game(self, game_id: int) -> list[Player]:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            result = await session.scalars(
                select(Player).where(Player.game_id == game_id)
            )
            return list(result.all())

    async def create_round(
        self, game_id: int, round_number: int, duration_seconds: int = 60
    ) -> Round:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        new_round = Round(
            game_id=game_id,
            round_number=round_number,
            current_status="open",
            deadline=datetime.utcnow() + timedelta(seconds=duration_seconds),
        )
        async with self.app.database.session() as session:
            session.add(new_round)
            await session.commit()
            await session.refresh(new_round)
            return new_round

    async def get_current_round(self, game_id: int) -> Round | None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            return await session.scalar(
                select(Round).where(
                    Round.game_id == game_id, Round.current_status == "open"
                )
            )

    async def create_move(
        self,
        round_id: int,
        move_type: str,
        player_id: int,
        stock_ticket: str,
        quantity: int,
    ) -> Move:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        new_move = Move(
            player_id=player_id,
            move_type=move_type,
            round_id=round_id,
            stock_ticket=stock_ticket,
            quantity=quantity,
        )
        async with self.app.database.session() as session:
            session.add(new_move)
            await session.commit()
            await session.refresh(new_move)
            return new_move

    async def get_moves_by_round(self, round_id: int) -> list[Move]:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            result = await session.scalars(
                select(Move).where(Move.round_id == round_id)
            )
            return list(result.all())

    async def update_stock_price(self, stock_id: int, new_price: int) -> None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            await session.execute(
                update(Stock)
                .where(Stock.id == stock_id)
                .values(current_price=new_price)
            )
            await session.commit()

    async def get_stocks_by_game(self, game_id: int) -> list[Stock]:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            result = await session.scalars(
                select(Stock).where(Stock.game_id == game_id)
            )
            return list(result.all())

    async def get_stock_by_ticket(
        self, game_id: int, ticket_name: str
    ) -> Stock | None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            return await session.scalar(
                select(Stock).where(
                    Stock.game_id == game_id, Stock.ticket_name == ticket_name
                )
            )

    async def get_player_portfolio(self, player_id: int) -> list[PlayerStock]:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            result = await session.scalars(
                select(PlayerStock).where(PlayerStock.player_id == player_id)
            )
            return list(result.all())

    async def try_close_round(self, round_id: int) -> bool:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            result = await session.execute(
                update(Round)
                .where(Round.id == round_id, Round.current_status == "open")
                .values(current_status="closed")
            )
            await session.commit()
            return result.rowcount == 1

    def init_round_completion(
        self, round_id: int, expected_player_ids: list[int]
    ) -> asyncio.Event:
        event = asyncio.Event()
        expected_set = set(expected_player_ids)
        self._round_completion_state[round_id] = {
            "event": event,
            "ready": set(),
            "expected": expected_set,
        }
        if not expected_set:
            event.set()
        return event

    def mark_player_ready_for_round(
        self, round_id: int, player_id: int
    ) -> tuple[str, int, int]:
        state = self._round_completion_state.get(round_id)
        if not state:
            return "not_managed", 0, 0
        expected: set[int] = state["expected"]
        ready: set[int] = state["ready"]
        if not expected:
            return "not_expected", len(ready), len(expected)
        if player_id not in expected:
            return "not_expected", len(ready), len(expected)
        if player_id in ready:
            return "already_ready", len(ready), len(expected)
        ready.add(player_id)
        if ready >= expected:
            state["event"].set()
            return "completed", len(ready), len(expected)
        return "waiting", len(ready), len(expected)

    def cleanup_round_completion(self, round_id: int) -> None:
        self._round_completion_state.pop(round_id, None)

    async def update_player_balance(self, player_id: int, delta: int) -> None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            player = await session.scalar(
                select(Player).where(Player.id == player_id)
            )
            if player:
                await session.execute(
                    update(Player)
                    .where(Player.id == player_id)
                    .values(balance=player.balance + delta)
                )
                await session.commit()

    async def conver_player_stock_to_balane(self, player_id: int):
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            clear_balance = (
                await session.scalar(
                    select(Player.balance).where(Player.id == player_id)
                )
                or 0
            )
            value_stmt = (
                select(func.sum(PlayerStock.quantity * Stock.current_price))
                .join(Stock, PlayerStock.stock_id == Stock.id)
                .where(PlayerStock.player_id == player_id)
            )
            portfolio_value = await session.scalar(value_stmt) or 0
            return clear_balance + portfolio_value

    async def upsert_player_stock(
        self, player_id: int, stock_id: int, quantity_delta: int
    ) -> None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            existing = await session.scalar(
                select(PlayerStock).where(
                    PlayerStock.player_id == player_id,
                    PlayerStock.stock_id == stock_id,
                )
            )
            if existing:
                await session.execute(
                    update(PlayerStock)
                    .where(
                        PlayerStock.player_id == player_id,
                        PlayerStock.stock_id == stock_id,
                    )
                    .values(quantity=existing.quantity + quantity_delta)
                )
            else:
                session.add(
                    PlayerStock(
                        player_id=player_id,
                        stock_id=stock_id,
                        quantity=quantity_delta,
                    )
                )
            await session.commit()

    async def create_stock(
        self, game_id: int, ticket_name: str, current_price: int
    ) -> Stock:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        new_stock = Stock(
            game_id=game_id,
            ticket_name=ticket_name,
            current_price=current_price,
        )
        async with self.app.database.session() as session:
            session.add(new_stock)
            await session.commit()
            await session.refresh(new_stock)
            return new_stock

    async def upsert_leaderboard_entry(
        self,
        game_id: int,
        player_id: int,
        player_tg_user_id: int,
        player_username: str | None,
        balance_delta: int,
    ) -> LeaderboardEntry:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            existing = await session.scalar(
                select(LeaderboardEntry)
                .where(LeaderboardEntry.player_tg_user_id == player_tg_user_id)
                .order_by(LeaderboardEntry.recorded_at.desc())
            )
            if existing:
                await session.execute(
                    update(LeaderboardEntry)
                    .where(LeaderboardEntry.id == existing.id)
                    .values(
                        final_balance=existing.final_balance + balance_delta,
                        player_tg_user_id=player_tg_user_id,
                        player_id=player_id,
                        player_username=player_username,
                        recorded_at=datetime.utcnow(),
                        game_id=game_id,
                    )
                )
                await session.commit()
                await session.refresh(existing)
                return existing

            new_entry = LeaderboardEntry(
                game_id=game_id,
                player_id=player_id,
                player_tg_user_id=player_tg_user_id,
                player_username=player_username,
                final_balance=balance_delta,
            )
            session.add(new_entry)
            await session.commit()
            await session.refresh(new_entry)
            return new_entry

    async def cleanup_game_resources(self, game_id: int) -> None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            round_ids = select(Round.id).where(Round.game_id == game_id)
            player_ids = select(Player.id).where(Player.game_id == game_id)
            await session.execute(
                delete(Move).where(Move.round_id.in_(round_ids))
            )
            await session.execute(
                delete(PlayerStock).where(PlayerStock.player_id.in_(player_ids))
            )
            await session.execute(delete(Round).where(Round.game_id == game_id))
            await session.execute(delete(Stock).where(Stock.game_id == game_id))
            await session.execute(
                delete(Player).where(Player.game_id == game_id)
            )
            await session.commit()

    async def get_game_by_chat_id(self, chat_id: int) -> Game | None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            stmt = (
                select(Game)
                .where(Game.chat_id == chat_id)
                .order_by(Game.id.desc())
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_round(self, round_id: int) -> Round | None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            return await session.scalar(
                select(Round).where(Round.id == round_id)
            )
