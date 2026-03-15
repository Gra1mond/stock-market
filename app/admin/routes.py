import typing

if typing.TYPE_CHECKING:
    from aiohttp.web_app import Application

from app.admin.views import AdminCurrentView, AdminLoginView

__all__ = ("register_admin_routes",)


def register_admin_routes(app: "Application") -> None:
    app.router.add_view("/admin/login", AdminLoginView)
    app.router.add_view("/admin/current", AdminCurrentView)
