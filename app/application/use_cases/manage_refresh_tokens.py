from datetime import datetime, timezone
import logging

from app.application.entities.refresh_token import RefreshTokenRecord
from app.application.ports.refresh_token_repository import RefreshTokenRepository
from app.core.errors import InvalidRefreshTokenError, RefreshTokenReuseDetectedError
from app.core.logging_utils import hash_value, log_event
from app.core.security import create_refresh_token, decode_token, validate_refresh_token

logger = logging.getLogger("ISafe.Auth")


class RefreshTokenService:
    @staticmethod
    async def register_refresh_token(token: str, repository: RefreshTokenRepository) -> RefreshTokenRecord:
        claims = validate_refresh_token(token)
        issued_at = RefreshTokenService._parse_timestamp(claims.get("iat")) or datetime.now(timezone.utc)
        expires_at = RefreshTokenService._parse_timestamp(claims["exp"])

        record = RefreshTokenRecord(
            jti=claims["jti"],
            sub=claims["sub"],
            token_type=claims["type"],
            issued_at=issued_at,
            expires_at=expires_at,
            parent_jti=claims.get("parent_jti"),
        )
        await repository.save(record)
        return record

    @staticmethod
    async def validate_refresh_token_not_revoked(token: str, repository: RefreshTokenRepository) -> dict:
        try:
            claims = validate_refresh_token(token)
        except ValueError as exc:
            raise InvalidRefreshTokenError("Refresh token inválido.") from exc
        record = await repository.get_by_jti(claims["jti"])

        if record is None:
            return claims
        if record.revoked_at is not None:
            raise InvalidRefreshTokenError("Refresh token revogado.")
        if record.expires_at <= datetime.now(timezone.utc):
            raise InvalidRefreshTokenError("Refresh token expirado.")
        return claims

    @staticmethod
    async def rotate_refresh_token(token: str, repository: RefreshTokenRepository) -> str:
        try:
            claims = validate_refresh_token(token)
        except ValueError as exc:
            raise InvalidRefreshTokenError("Refresh token inválido.") from exc
        record = await repository.get_by_jti(claims["jti"])

        if record and record.revoked_at is not None:
            await RefreshTokenService.detect_reuse_attack(token, repository)
            raise RefreshTokenReuseDetectedError("Refresh token reutilizado. Sessão marcada como suspeita.")

        if record and record.expires_at <= datetime.now(timezone.utc):
            raise InvalidRefreshTokenError("Refresh token expirado.")

        await repository.revoke(claims["jti"], reason="rotated")
        log_event(logger, logging.INFO, "refresh_rotated", sub_hash=hash_value(claims["sub"]), jti=claims["jti"])

        new_token = create_refresh_token(
            {"sub": claims["sub"], "parent_jti": claims["jti"]}
        )
        await RefreshTokenService.register_refresh_token(new_token, repository)
        return new_token

    @staticmethod
    async def detect_reuse_attack(token: str, repository: RefreshTokenRepository) -> dict:
        try:
            claims = validate_refresh_token(token)
        except ValueError as exc:
            raise InvalidRefreshTokenError("Refresh token inválido.") from exc
        await repository.mark_compromised(claims["jti"], reason="reuse_attack")
        await repository.revoke_subject_tokens(claims["sub"], reason="reuse_attack")
        log_event(logger, logging.WARNING, "refresh_reuse_attack", sub_hash=hash_value(claims["sub"]), jti=claims["jti"])
        return claims

    @staticmethod
    async def revoke_refresh_token_by_jti(
        jti: str,
        repository: RefreshTokenRepository,
        reason: str | None = None,
    ) -> RefreshTokenRecord | None:
        return await repository.revoke(jti, reason=reason)

    @staticmethod
    def _parse_timestamp(value: int | float | None) -> datetime | None:
        if value is None:
            return None
        return datetime.fromtimestamp(value, tz=timezone.utc)
