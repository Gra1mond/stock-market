import importlib
import typing

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.store.database.sqlalchemestry_base import BaseModel

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Database:
    def __init__(self, app: "Application"):
        self.app = app
        self._engine = None
        self._session_factory: async_sessionmaker | None = None

    async def connect(self, *args, **kwargs) -> None:
        if not self.app.config.database:
            return
        db = self.app.config.database
        database_url = (
            f"postgresql+asyncpg://{db.user}:{db.password}"
            f"@{db.host}:{db.port}/{db.database}"
        )
        self._engine = create_async_engine(database_url, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False
        )

        importlib.import_module("app.game.models")
        importlib.import_module("app.users.models")

        async with self._engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)

    async def disconnect(self, *args, **kwargs):
        if self._engine:
            self._engine.dispose()
            self._engine = None

    def session(self) -> AsyncSession:
        return self._session_factory()
