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

    async def create_player(self, tg_user_id: int, game_id: int, balance: int = 1000) -> Player:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        new_player = Player(game_id=game_id, tg_user_id=tg_user_id, balance=balance)
        async with self.app.database.session() as session:
            session.add(new_player)
            await session.commit()
            await session.refresh(new_player)
            return new_player

    async def get_player(self, tg_user_id: int, game_id: int | None = None) -> Player | None:
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

    async def create_move(self, round_id: int, move_type: str, player_id: int, stock_ticket: str, quantity: int) -> Move:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        new_move = Move(player_id=player_id, move_type=move_type, round_id=round_id, stock_ticket=stock_ticket, quantity=quantity)
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
    async def get_stocks_by_game(self, game_id: int) -> list[Stock]:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            result = await session.scalars(select(Stock).where(Stock.game_id == game_id))
            return list(result.all())

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

    async def update_player_balance(self, player_id: int, delta: int) -> None:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        async with self.app.database.session() as session:
            player = await session.scalar(select(Player).where(Player.id == player_id))
            if player:
                await session.execute(
                    update(Player)
                    .where(Player.id == player_id)
                    .values(balance=player.balance + delta)
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
    
    async def create_stock(self, game_id: int, ticket_name: str, current_price: int) -> Stock:
        if not self.app.database.session:
            raise RuntimeError("Database session is not started")
        new_stock = Stock(game_id=game_id, ticket_name=ticket_name, current_price=current_price)
        async with self.app.database.session() as session:
            session.add(new_stock)
            await session.commit()
            await session.refresh(new_stock)
            return new_stock

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
            game = result.scalars().first()
            return game
            
