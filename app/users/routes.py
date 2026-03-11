import typing
if typing.TYPE_CHECKING:
    from aiohttp.web_app import Application

__all__ = ("register_urls",)


def setup_routes(app: "Application"):
    from app.users.views import UsersLoginView, UsersCurrentView

    app.router.add_view("/users.login", UsersLoginView)
    app.router.add_view("/users.current", UsersCurrentView)
