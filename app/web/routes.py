from aiohttp.web_app import Application

from app.admin.routes import register_admin_routes
from app.store.bot.routes import setup_routes as bot_setup_routes
from app.users.routes import setup_routes as users_setup_route

__all__ = ("setup_routes",)


def setup_routes(app: Application):
    bot_setup_routes(app)
    users_setup_route(app)
    register_admin_routes(app)
