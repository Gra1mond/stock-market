from aiohttp.web import json_response
from aiohttp_session import get_session
from marshmallow import ValidationError

from app.users.schema import UserLoginSchema, UserResponseSchema
from app.web.app import View


class UsersLoginView(View):
    async def post(self):
        data = await self.data()

        try:
            validated = UserLoginSchema().load(data)
        except ValidationError as exc:
            return json_response(status=400, data={"errors": exc.messages})

        username = validated["username"]

        user = await self.store.user.get_by_user_id(username)
        if not user:
            return json_response(status=404, data={"error": "User not found"})
        session = await get_session(self.request)
        session["user_id"] = user.id
        payload = UserResponseSchema().dump(user)
        return json_response(data=payload)


class UsersCurrentView(View):
    async def get(self):
        if self.request.users is None:
            return json_response(status=401, data="Not authenticated")
        payload = UserResponseSchema().dump(self.request.users)
        return json_response(data=payload)
