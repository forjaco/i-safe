from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class MaxRequestSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > settings.HTTP_MAX_REQUEST_SIZE_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Payload excede o limite de segurança permitido."},
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Cabeçalho Content-Length inválido."},
                )
        return await call_next(request)
