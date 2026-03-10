from aiohttp.web_middlewares import middleware
from aiohttp_session import get_session
import typing
if typing.TYPE_CHECKING:
    from app.web.app import Request


