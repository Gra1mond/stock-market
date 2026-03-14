import asyncio
import logging

from app.bot.handlers import GameHandler
import typing
if typing.TYPE_CHECKING:
    from app.web.app import Application

logger = logging.getLogger(__name__)


async def _polling_loop(app: "Application") -> None:
    handler = GameHandler(app)
    offset: int | None = None
    while True:
        try:
            updates = await app.store.bot.get_updates(offset=offset, timeout=30)
        except Exception:
            logger.exception("Telegram polling failed, retrying in 5s")
            await asyncio.sleep(5)
            continue

        if not updates:
            continue

        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]
            tg_user_id = message["from"]["id"]
            username = message["from"].get("username")
            if not username:
                username = message["from"].get("first_name")
            text = message.get("text", "")

            try:
                await handler.handle(
                    chat_id=chat_id,
                    tg_user_id=tg_user_id,
                    username=username,
                    text=text,
                )
            except Exception:
                logger.exception("Failed to handle telegram update %s", update.get("update_id"))


async def start_polling(app: "Application") -> None:
    task = asyncio.create_task(_polling_loop(app))
    app["polling_task"] = task


async def stop_polling(app: "Application") -> None:
    task = app.get("polling_task")
    if not task:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
