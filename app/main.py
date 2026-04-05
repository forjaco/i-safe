from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import uuid
from app.core.config import settings
from app.core.http_middleware import MaxRequestSizeMiddleware
from app.core.logging_utils import reset_request_id, set_request_id
from app.infrastructure.database.auth_db import get_auth_session_factory
from app.presentation.api.auth import router as auth_router
from app.presentation.api.endpoints import router as osint_router
from app.presentation.api.upload import router as upload_router

app = FastAPI(title=settings.APP_NAME)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(MaxRequestSizeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Forwarded-For", "X-Request-ID"],
)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(osint_router, prefix="/api/v1/osint", tags=["Monitoramento"])
app.include_router(upload_router, prefix="/api/v1/privacy", tags=["Privacidade"])


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}


@app.get("/ready")
async def readiness():
    try:
        get_auth_session_factory()
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "dependencies": {"auth_storage": "unavailable"}},
        )

    return {
        "status": "ready",
        "dependencies": {
            "auth_storage": "ok",
            "osint_persistence": "enabled" if settings.OSINT_PERSIST_RESULTS else "diagnostic_disabled",
        },
    }


@app.middleware("http")
async def set_security_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id
    token = set_request_id(request_id)
    try:
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        if request.url.path in {"/health", "/ready"}:
            response.headers["Cache-Control"] = "no-store, max-age=0"
        elif request.url.path.startswith("/api/v1/auth"):
            response.headers["Cache-Control"] = "no-store"
        else:
            response.headers["Cache-Control"] = "no-store"
        return response
    finally:
        reset_request_id(token)
