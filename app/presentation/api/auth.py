import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from app.application.ports.refresh_token_repository import RefreshTokenRepository
from app.application.ports.user_repository import UserRepository
from app.application.use_cases.authenticate_user import AuthenticationService
from app.core.abuse_prevention import abuse_prevention_service
from app.core.config import settings
from app.core.errors import (
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    PersistenceUnavailableError,
    RefreshTokenReuseDetectedError,
)
from app.core.logging_utils import log_event
from app.core.security import validate_access_token
from app.infrastructure.database.auth_db import get_auth_session_factory
from app.infrastructure.repositories.sqlalchemy_refresh_token_repository import SQLAlchemyRefreshTokenRepository
from app.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository


router = APIRouter()
logger = logging.getLogger("ISafe.Auth.API")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LogoutResponse(BaseModel):
    status: str


class CurrentUserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool


async def get_user_repository() -> UserRepository:
    try:
        session_factory = get_auth_session_factory()
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço indisponível no momento.") from exc
    return SQLAlchemyUserRepository(session_factory)


async def get_refresh_token_repository() -> RefreshTokenRepository:
    try:
        session_factory = get_auth_session_factory()
    except PersistenceUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço indisponível no momento.") from exc
    return SQLAlchemyRefreshTokenRepository(session_factory)


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_COOKIE_PATH,
    )


def _extract_refresh_token(request: Request) -> str:
    cookie_token = request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    if not settings.effective_refresh_header_fallback:
        raise InvalidRefreshTokenError("Refresh token ausente.")

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token:
        return token.strip()

    raise InvalidRefreshTokenError("Refresh token ausente.")


def _extract_access_token(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token:
        return token.strip()
    raise InvalidAccessTokenError("Access token ausente.")


async def get_current_user(
    request: Request,
    user_repository: UserRepository = Depends(get_user_repository),
):
    try:
        access_token = _extract_access_token(request)
        return await AuthenticationService.get_authenticated_user(access_token, user_repository)
    except InvalidAccessTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token inválido.") from exc


def get_optional_authenticated_subject(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    try:
        claims = validate_access_token(token.strip())
    except ValueError:
        return None
    return str(claims["sub"])


def _raise_rate_limit(decision, response: Response) -> None:
    headers = {}
    if decision.retry_after_seconds:
        headers["Retry-After"] = str(decision.retry_after_seconds)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Muitas tentativas. Aguarde antes de tentar novamente.",
        headers=headers,
    )


@router.post("/login", response_model=AccessTokenResponse)
async def login_endpoint(
    request: Request,
    payload: LoginRequest,
    response: Response,
    user_repository: UserRepository = Depends(get_user_repository),
    refresh_repository: RefreshTokenRepository = Depends(get_refresh_token_repository),
):
    actor_id = abuse_prevention_service.actor_id_from_request(request)
    decision = abuse_prevention_service.evaluate_auth_login(actor_id, payload.email)
    if decision.blocked:
        _raise_rate_limit(decision, response)

    try:
        access_token, refresh_token = await AuthenticationService.login(
            payload.email,
            payload.password,
            user_repository,
            refresh_repository,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.") from exc
    except PersistenceUnavailableError as exc:
        log_event(logger, logging.ERROR, "auth_storage_unavailable")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço indisponível no momento.") from exc

    _set_refresh_cookie(response, refresh_token)
    return AccessTokenResponse(access_token=access_token)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_endpoint(
    request: Request,
    response: Response,
    refresh_repository: RefreshTokenRepository = Depends(get_refresh_token_repository),
):
    actor_id = abuse_prevention_service.actor_id_from_request(request)
    decision = abuse_prevention_service.evaluate_auth_refresh(actor_id)
    if decision.blocked:
        _raise_rate_limit(decision, response)

    try:
        refresh_token = _extract_refresh_token(request)
        access_token, rotated_refresh_token = await AuthenticationService.refresh_session(
            refresh_token,
            refresh_repository,
        )
    except RefreshTokenReuseDetectedError as exc:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida. Faça login novamente.") from exc
    except InvalidRefreshTokenError as exc:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido.") from exc
    except PersistenceUnavailableError as exc:
        log_event(logger, logging.ERROR, "auth_storage_unavailable")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço indisponível no momento.") from exc

    _set_refresh_cookie(response, rotated_refresh_token)
    return AccessTokenResponse(access_token=access_token)


@router.post("/logout", response_model=LogoutResponse)
async def logout_endpoint(
    request: Request,
    response: Response,
    refresh_repository: RefreshTokenRepository = Depends(get_refresh_token_repository),
):
    actor_id = abuse_prevention_service.actor_id_from_request(request)
    decision = abuse_prevention_service.evaluate_auth_logout(actor_id)
    if decision.blocked:
        _raise_rate_limit(decision, response)

    try:
        refresh_token = _extract_refresh_token(request)
        await AuthenticationService.logout(refresh_token, refresh_repository)
    except InvalidRefreshTokenError as exc:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido.") from exc
    except PersistenceUnavailableError as exc:
        log_event(logger, logging.ERROR, "auth_storage_unavailable")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço indisponível no momento.") from exc

    _clear_refresh_cookie(response)
    return LogoutResponse(status="logged_out")


@router.get("/me", response_model=CurrentUserResponse)
async def me_endpoint(current_user = Depends(get_current_user)):
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
    )
