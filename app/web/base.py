from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)

from app.admin.models import AdminModel
from app.store import Store
from app.store.database.database import Database
from app.users.models import UserModel
from app.web.config import Config

__all__ = ("Application", "Request", "View")


class Application(AiohttpApplication):
    config = Config
    store = Store
    database = Database


class Request(AiohttpRequest):
    users: UserModel | None = None
    _invalid_session: bool = False
    admin: AdminModel | None = None

    @property
    def app(self) -> Application:
        return super().app


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def database(self):
        return self.request.app.database

    @property
    def store(self) -> Store:
        return self.request.app.store

    async def data(self) -> dict:
        return await self.request.json()
