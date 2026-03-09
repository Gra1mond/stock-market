from aiohttp.web_middlewares import middleware
from aiohttp_session import get_session
import typing
if typing.TYPE_CHECKING:
    from app.web.app import Request


@middleware
async def auth_middleware(request: "Request", handler):
    # Получаем сессию
    session = await get_session(request)
    user_id = session.get("user_id")
    
    # Подставляем пользователя, если есть
    if user_id:
        user = await request.app.store.(user_id)
        request.users = user
    else:
        request.users = None
    
    return await handler(request)