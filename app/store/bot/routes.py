import typing

if typing.TYPE_CHECKING:
    from aiohttp.web_app import Application

__all__ = ("setup_routes",)


def setup_routes(app: "Application"):
    from app.bot.views import BotView

    app.router.add_view("/tg/webhook", BotView)
