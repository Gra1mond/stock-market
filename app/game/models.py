from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.store.database.sqlalchemestry_base import BaseModel


class Game(BaseModel):
    __tablename__ = "game"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    state: Mapped[str] = mapped_column(nullable=False)
    rounds: Mapped[list["Round"]] = relationship("Round", back_populates="game")
    players: Mapped[list["Player"]] = relationship("Player", back_populates="game")


class Player(BaseModel):
    __tablename__ = "player"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey("game.id"), nullable=False)
    tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance: Mapped[int] = mapped_column()
    tg_username: Mapped[str | None] = mapped_column(nullable=True)
    game: Mapped["Game"] = relationship("Game", back_populates="players")
    stock_portfolio: Mapped[list["PlayerStock"]] = relationship("PlayerStock", back_populates="player")


class Stock(BaseModel):
    __tablename__ = "stock"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey("game.id"), nullable=False)
    ticket_name: Mapped[str] = mapped_column(nullable=False)
    current_price: Mapped[int] = mapped_column()


class Round(BaseModel):
    __tablename__ = "round"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey("game.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(nullable=False)
    current_status: Mapped[str] = mapped_column()
    deadline: Mapped[datetime] = mapped_column()
    game: Mapped["Game"] = relationship("Game", back_populates="rounds")


class Move(BaseModel):
    __tablename__ = "move"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"), nullable=False)
    round_id: Mapped[int] = mapped_column(ForeignKey("round.id"), nullable=False)
    move_type: Mapped[str] = mapped_column(nullable=False)
    stock_ticket: Mapped[str] = mapped_column()
    quantity: Mapped[int] = mapped_column()


class PlayerStock(BaseModel):
    __tablename__ = "player_stock"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"), nullable=False)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stock.id"), nullable=False)
    quantity: Mapped[int] = mapped_column()
    player: Mapped["Player"] = relationship("Player", back_populates="stock_portfolio")


class LeaderboardEntry(BaseModel):
    __tablename__ = "leaderboard_entry"
    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey("game.id"), nullable=False)
    player_id: Mapped[int] = mapped_column(nullable=False)
    player_tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    player_username: Mapped[str | None] = mapped_column(nullable=True)
    final_balance: Mapped[int] = mapped_column()
    recorded_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
