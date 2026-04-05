import logging

from app.application.ports.refresh_token_repository import RefreshTokenRepository
from app.application.ports.user_repository import UserRepository
from app.application.use_cases.manage_refresh_tokens import RefreshTokenService
from app.core.errors import InvalidAccessTokenError, InvalidCredentialsError, InvalidRefreshTokenError, RefreshTokenReuseDetectedError
from app.core.logging_utils import hash_value, log_event
from app.core.security import create_access_token, create_refresh_token, decode_token, validate_access_token, validate_refresh_token, verify_password


logger = logging.getLogger("ISafe.Auth")


class AuthenticationService:
    @staticmethod
    async def get_authenticated_user(
        access_token: str,
        user_repository: UserRepository,
    ):
        try:
            claims = validate_access_token(access_token)
        except ValueError as exc:
            raise InvalidAccessTokenError("Access token inválido.") from exc

        normalized_email = claims["sub"].strip().lower()
        user = await user_repository.get_by_email(normalized_email)
        if user is None or not user.is_active:
            raise InvalidAccessTokenError("Access token inválido.")
        return user

    @staticmethod
    async def login(
        email: str,
        password: str,
        user_repository: UserRepository,
        refresh_repository: RefreshTokenRepository,
    ) -> tuple[str, str]:
        normalized_email = email.strip().lower()
        user = await user_repository.get_by_email(normalized_email)
        subject_hash = hash_value(normalized_email)

        if user is None or not user.is_active or not verify_password(password, user.hashed_password):
            log_event(logger, logging.WARNING, "auth_login_failed", subject_hash=subject_hash)
            raise InvalidCredentialsError("Credenciais inválidas.")

        access_token = create_access_token({"sub": user.email})
        refresh_token = create_refresh_token({"sub": user.email})
        await RefreshTokenService.register_refresh_token(refresh_token, refresh_repository)
        log_event(logger, logging.INFO, "auth_login_succeeded", subject_hash=subject_hash)
        return access_token, refresh_token

    @staticmethod
    async def refresh_session(
        refresh_token: str,
        refresh_repository: RefreshTokenRepository,
    ) -> tuple[str, str]:
        try:
            claims = validate_refresh_token(refresh_token)
            rotated_refresh_token = await RefreshTokenService.rotate_refresh_token(refresh_token, refresh_repository)
        except RefreshTokenReuseDetectedError:
            raise
        except ValueError as exc:
            raise InvalidRefreshTokenError("Refresh token inválido.") from exc

        access_token = create_access_token({"sub": claims["sub"]})
        log_event(logger, logging.INFO, "auth_refresh_succeeded", subject_hash=hash_value(claims["sub"]))
        return access_token, rotated_refresh_token

    @staticmethod
    async def logout(
        refresh_token: str,
        refresh_repository: RefreshTokenRepository,
    ) -> None:
        try:
            claims = await RefreshTokenService.validate_refresh_token_not_revoked(refresh_token, refresh_repository)
        except ValueError as exc:
            raise InvalidRefreshTokenError("Refresh token inválido.") from exc

        await RefreshTokenService.revoke_refresh_token_by_jti(claims["jti"], refresh_repository, reason="logout")
        log_event(logger, logging.INFO, "auth_logout_succeeded", subject_hash=hash_value(claims["sub"]))

    @staticmethod
    def get_refresh_token_jti(refresh_token: str) -> str:
        claims = decode_token(refresh_token)
        return str(claims["jti"])
