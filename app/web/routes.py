from aiohttp.web_app import Application

__all__ = ("setup_routes",)


def setup_routes(app: Application):
    from app.users.routes import setup_routes as users_setup_route

    users_setup_route(app)
