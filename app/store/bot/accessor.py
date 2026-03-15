import typing

import aiohttp

from app.base.base_accessor import BaseAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application
"""Перенести в отдельный файл"""
API_URL = "https://api.telegram.org/bot{token}/{method}"


class BotAccessor(BaseAccessor):
    def __init__(self, app: "Application"):
        super().__init__(app)
        self._session: aiohttp.ClientSession | None = None

    async def connect(self, app: "Application") -> None:
        self._session = aiohttp.ClientSession()

    async def disconnect(self, app: "Application") -> None:
        if self._session:
            await self._session.close()

    def _url(self, method: str) -> str:
        return API_URL.format(token=self.app.config.bot.token, method=method)

    async def send_message(
        self, chat_id: int, text: str, reply_markup: dict | None = None
    ) -> None:
        payload: dict[str, object] = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        await self._session.post(self._url("sendMessage"), json=payload)

    """для этого нужен домен"""

    async def set_webhook(self, url: str) -> None:
        await self._session.post(
            self._url("setWebhook"),
            json={"url": url},
        )

    async def get_updates(
        self, offset: int | None = None, timeout: int = 30
    ) -> list[dict]:
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset

        response = await self._session.get(
            self._url("getUpdates"), params=params
        )
        response.raise_for_status()
        payload = await response.json()
        return payload.get("result", [])
