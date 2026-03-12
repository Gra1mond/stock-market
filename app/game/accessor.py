from datetime import datetime, timedelta

from sqlalchemy import select, update

from app.base.base_accessor import BaseAccessor
from app.game.models import Game, Move, Player, PlayerStock, Round, Stock
from app.game.states import GameState
import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


class GameAccessor(BaseAccessor):
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

    async def create_player(self, tg_user_id: int, game_id: int) -> Player:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        new_player = Player(game_id=game_id, tg_user_id=tg_user_id)
        async with self.app.database.session() as session:
            session.add(new_player)
            await session.commit()
            await session.refresh(new_player)
            return new_player

    async def get_player(self, tg_user_id: int) -> Player | None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            return await session.scalar(select(Player).where(Player.tg_user_id == tg_user_id))

    async def get_players_by_game(self, game_id: int) -> list[Player]:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            result = await session.scalars(select(Player).where(Player.game_id == game_id))
            return list(result.all())

    async def create_round(self, game_id: int, round_number: int, duration_seconds: int = 60) -> Round:
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
            return await session.scalar(select(Round).where(Round.game_id == game_id, Round.current_status == "open"))

    async def create_move(self, round_id: int, move_type: str, player_id: int) -> Move:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        new_move = Move(player_id=player_id, move_type=move_type, round_id=round_id)
        async with self.app.database.session() as session:
            session.add(new_move)
            await session.commit()
            await session.refresh(new_move)
            return new_move

    async def get_moves_by_round(self, round_id: int) -> list[Move]:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            result = await session.scalars(select(Move).where(Move.round_id == round_id))
            return list(result.all())

    async def update_stock_price(self, stock_id: int, new_price: int) -> None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            await session.execute(
                update(Stock).where(Stock.id == stock_id).values(current_price=new_price)
            )
            await session.commit()
    async def upsert_player_stock(self, player_id: int, stock_id: int, quantity_delta: int) -> None:
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
                    .where(PlayerStock.player_id == player_id, PlayerStock.stock_id == stock_id)
                    .values(quantity=existing.quantity + quantity_delta)
                )
            else:
                session.add(PlayerStock(player_id=player_id, stock_id=stock_id, quantity=quantity_delta))
            await session.commit()
