from aiohttp_session import get_session

from app.web.app import View
from aiohttp.web import json_response
class UsersLoginView(View):

    async def post(self):

        data = await self.data()

        input_url = data.get("url")
        username = data.get("username")

        user = await self.store.user.get_by_user_id(input_url)
        if not user:
            return """Дописать error (можно в отдельный файл)"""
        session = await get_session(self.request)
        session["user_id"] = user.id
        return json_response(data={"id": user.id, "username": user.username})

class UsersCurrentView(View):

    async def get(self):
        if self.request.users is None:
            return json_response(
                status=401,
                data="Not authenticated",
            )
        return json_response(
            data={"Username":self.request.users.username,"id":self.request.users.id}
        )
