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
        text: str = message.get("text", "")

        handler = GameHandler(self.request.app)
        await handler.handle(chat_id=chat_id, tg_user_id=tg_user_id, text=text)

        return Response(status=200)
