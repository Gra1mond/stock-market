import typing
if typing.TYPE_CHECKING:
    from aiohttp.web_app import Application

__all__ = ("register_urls",)


def setup_routes(app: "Application"):
    from app.users.views import UsersLoginView
    
    app.router.add_route("/users.login",UsersLoginView)
