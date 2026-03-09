from typing import Optional

from aiohttp.web import (
    Application as AiohttpApplication,
    View as AiohttpView,
    Request as AiohttpRequest
)
from app.store import Store
from app.store.store import setup_store
from app.users.models import UserModel
from app.web.config import Config

from app.store.database.database import Database

from .routes import setup_routes

__all__ = ("Application",)


class Application(AiohttpApplication):
    config = Config
    store = Store
    database = Database

class Request(AiohttpRequest):
    users: Optional[UserModel] = None
    _invalid_session: bool = False
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
    def store(self)->Store:
        return self.request.app.store
    
    async def data(self) -> dict:
        return await self.request.json("data",{})



app = Application()


def setup_app(config_path: str) -> Application:
    setup_routes(app)
    setup_store(app)
    return app
