import json
import typing

from aiohttp.web_exceptions import HTTPException, HTTPUnprocessableEntity
from aiohttp.web_middlewares import middleware
from aiohttp_apispec import validation_middleware
from aiohttp_session import get_session
from sqlalchemy import select

from app.admin.models import AdminModel

if typing.TYPE_CHECKING:
    from app.web.app import Application, Request
from app.web.utils import error_json_response

AUTH_EXEMPT_PATHS = {"/users.login", "/admin/login", "/docs"}


HTTP_ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "not_implemented",
    409: "conflict",
    500: "internal_server_error",
}


@middleware
async def auth_middleware(request: "Request", handler):
    session = await get_session(request)
    admin_id = session.get("admin_id")

    if admin_id:
        if request.app.database.session:
            async with request.app.database.session() as db_session:
                admin_obj = await db_session.scalar(
                    select(AdminModel).where(AdminModel.id == admin_id)
                )
                if admin_obj:
                    request.admin = admin_obj
                else:
                    session.pop("admin_id", None)
                    request.admin = None
                    request._invalid_session = True
        else:
            session.pop("admin_id", None)
            request.admin = None
            request._invalid_session = True
    else:
        request.admin = None
        request._invalid_session = False

    return await handler(request)


@middleware
async def error_handling_middleware(request: "Request", handler):
    try:
        response = await handler(request)
    except HTTPUnprocessableEntity as e:
        return error_json_response(
            http_status=400,
            status=HTTP_ERROR_CODES[400],
            message=e.reason,
            data=json.loads(e.text),
        )
    except HTTPException as e:
        return error_json_response(
            http_status=e.status,
            status=HTTP_ERROR_CODES.get(e.status, "error"),
            message=str(e),
        )
    except Exception as e:
        request.app.logger.error("Exception", exc_info=e)
        return error_json_response(
            http_status=500, status="internal_server_error", message=str(e)
        )

    return response


def setup_middlewares(app: "Application"):
    app.middlewares.append(auth_middleware)
    app.middlewares.append(error_handling_middleware)
    app.middlewares.append(validation_middleware)
