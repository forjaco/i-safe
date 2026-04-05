from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.application.entities.refresh_token import RefreshTokenRecord
from app.infrastructure.database.models import RefreshTokenRecordModel


class SQLAlchemyRefreshTokenRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    async def save(self, token_record: RefreshTokenRecord) -> None:
        with self._session_factory() as session:
            model = RefreshTokenRecordModel(
                jti=token_record.jti,
                sub=token_record.sub,
                token_type=token_record.token_type,
                issued_at=token_record.issued_at,
                expires_at=token_record.expires_at,
                parent_jti=token_record.parent_jti,
                revoked_at=token_record.revoked_at,
                compromised_at=token_record.compromised_at,
                reason=token_record.reason,
            )
            session.merge(model)
            session.commit()

    async def get_by_jti(self, jti: str) -> RefreshTokenRecord | None:
        with self._session_factory() as session:
            model = session.get(RefreshTokenRecordModel, jti)
            return self._to_entity(model) if model else None

    async def revoke(self, jti: str, reason: str | None = None) -> RefreshTokenRecord | None:
        with self._session_factory() as session:
            model = session.get(RefreshTokenRecordModel, jti)
            if model is None:
                return None
            model.revoked_at = model.revoked_at or self._utcnow()
            model.reason = reason
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    async def revoke_subject_tokens(self, sub: str, reason: str | None = None) -> None:
        with self._session_factory() as session:
            result = session.execute(select(RefreshTokenRecordModel).where(RefreshTokenRecordModel.sub == sub))
            now = self._utcnow()
            for model in result.scalars():
                if model.revoked_at is None:
                    model.revoked_at = now
                model.reason = reason
            session.commit()

    async def mark_compromised(self, jti: str, reason: str | None = None) -> RefreshTokenRecord | None:
        with self._session_factory() as session:
            model = session.get(RefreshTokenRecordModel, jti)
            if model is None:
                return None
            model.compromised_at = self._utcnow()
            if reason:
                model.reason = reason
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    @staticmethod
    def _to_entity(model: RefreshTokenRecordModel) -> RefreshTokenRecord:
        return RefreshTokenRecord(
            jti=model.jti,
            sub=model.sub,
            token_type=model.token_type,
            issued_at=SQLAlchemyRefreshTokenRepository._ensure_utc(model.issued_at),
            expires_at=SQLAlchemyRefreshTokenRepository._ensure_utc(model.expires_at),
            parent_jti=model.parent_jti,
            revoked_at=SQLAlchemyRefreshTokenRepository._ensure_utc(model.revoked_at),
            compromised_at=SQLAlchemyRefreshTokenRepository._ensure_utc(model.compromised_at),
            reason=model.reason,
        )

    @staticmethod
    def _utcnow():
        from datetime import datetime, timezone

        return datetime.now(timezone.utc)

    @staticmethod
    def _ensure_utc(value):
        if value is None:
            return None
        if value.tzinfo is None:
            from datetime import timezone

            return value.replace(tzinfo=timezone.utc)
        return value
