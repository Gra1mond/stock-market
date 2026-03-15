from hashlib import sha256

from aiohttp.web_response import json_response
from aiohttp_apispec import request_schema, response_schema
from aiohttp_session import get_session

from app.admin.schemes import AdminSchema
from app.web.app import View
from app.web.utils import error_json_response


class AdminLoginView(View):
    @request_schema(AdminSchema)
    @response_schema(AdminSchema, 200)
    async def post(self):
        data = await self.data()
        email = data.get("email")
        password = data.get("password")
        tg_user_id = data.get("tg_user_id")

        admin = await self.store.admins.get_by_email(email)
        if not admin:
            return error_json_response(
                http_status=403,
                status="forbidden",
                message="Invalid credentials",
            )

        hashed_password = sha256(password.encode()).hexdigest()
        if admin.password != hashed_password:
            return error_json_response(
                http_status=403,
                status="forbidden",
                message="Invalid credentials",
            )

        if admin.tg_user_id != tg_user_id:
            return error_json_response(
                http_status=403,
                status="forbidden",
                message="Telegram user is not authorized",
            )

        session = await get_session(self.request)
        session["admin_id"] = admin.id

        return json_response(data={"id": admin.id, "email": admin.email})


class AdminCurrentView(View):
    @response_schema(AdminSchema, 200)
    async def get(self):
        if not hasattr(self.request, "admin") or self.request.admin is None:
            return error_json_response(
                http_status=401,
                status="unauthorized",
                message="Not authenticated",
            )

        return json_response(
            data={
                "id": self.request.admin.id,
                "email": self.request.admin.email,
            }
        )
