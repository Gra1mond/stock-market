from aiohttp.web_response import Response

from app.bot.handlers import GameHandler
from app.web.app import View


class BotView(View):
    async def post(self) -> Response:
        data = await self.request.json()
        message = data.get("message")
        if not message:
            return Response(status=200)

        chat_id: int = message["chat"]["id"]
        tg_user_id: int = message["from"]["id"]
        username = message["from"].get("username")
        if not username:
            username = message["from"].get("first_name")
        text: str = message.get("text", "")

        handler = GameHandler(self.request.app)
        await handler.handle(chat_id=chat_id, tg_user_id=tg_user_id, username=username, text=text)

        return Response(status=200)
