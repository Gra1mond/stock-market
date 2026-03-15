from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from app.admin.models import AdminModel
from app.bot.polling import start_polling, stop_polling
from app.store import Store
from app.store.database.database import Database
from app.store.store import setup_store
from app.users.models import UserModel
from app.web.config import Config
from app.web.middlewares import setup_middlewares

from .config import setup_config

__all__ = ("Application",)


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


app = Application()


def setup_app(config_path: str) -> Application:
    from .routes import setup_routes

    setup_config(app, config_path)
    setup_routes(app)
    setup_aiohttp_apispec(
        app=app,
        title="Stock Market API",
        version="1.0",
        url="/docs/swagger.json",
        swagger_path="/docs",
    )
    session_key = app.config.session.key
    setup(app, EncryptedCookieStorage(session_key))
    setup_middlewares(app)
    setup_store(app)
    app.on_startup.append(start_polling)
    app.on_cleanup.append(stop_polling)
    return app
