import typing
from sqlalchemy.ext.asyncio import async_sessionmaker,create_async_engine,AsyncSession

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Database:
    def __init__(self,app:Application):
        self.app = app
        self._engine = None
        self._session_factory: async_sessionmaker | None = None

    async def connect(self,*args,**kwargs)->None:
        if not self.app.config.database:
            return
        database_url = None
        """Исправить заглушку при подключении к базе"""
        self._engine = create_async_engine(database_url)
        self._session_factory = async_sessionmaker(self._engine,expire_on_commit=False)

    async def disconnect(self,*args,**kwargs):
        if self._engine:
            self._engine.dispose()
            self._engine = None

    def session(self)->AsyncSession:
        return self._session_factory()


        