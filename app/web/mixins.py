from aiohttp.web import HTTPUnauthorized, HTTPForbidden
from aiohttp.abc import StreamResponse
from app.web.app import Request, View  # импортируем View тоже

"""class AuthRequiredMixin:
    request: Request  
    
    async def _iter(self) -> StreamResponse:
        if self.request.users is None:
            if getattr(self.request, "_invalid_session", False):
                raise HTTPForbidden
            raise HTTPUnauthorized
        return await super()._iter()"""