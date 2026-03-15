
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from app.bot.polling import start_polling, stop_polling
from app.store.store import setup_store
from app.web.middlewares import setup_middlewares

from .base import Application, Request, View
from .config import setup_config
from .routes import setup_routes

__all__ = ("Application", "Request", "View")


app = Application()


def setup_app(config_path: str) -> Application:
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
