from datetime import datetime, timezone

from app.application.entities.refresh_token import RefreshTokenRecord


class InMemoryRefreshTokenRepository:
    def __init__(self):
        self._records: dict[str, RefreshTokenRecord] = {}

    async def save(self, token_record: RefreshTokenRecord) -> None:
        self._records[token_record.jti] = token_record

    async def get_by_jti(self, jti: str) -> RefreshTokenRecord | None:
        return self._records.get(jti)

    async def revoke(self, jti: str, reason: str | None = None) -> RefreshTokenRecord | None:
        record = self._records.get(jti)
        if record is None:
            return None

        record.revoked_at = datetime.now(timezone.utc)
        record.reason = reason
        return record

    async def revoke_subject_tokens(self, sub: str, reason: str | None = None) -> None:
        now = datetime.now(timezone.utc)
        for record in self._records.values():
            if record.sub == sub and record.revoked_at is None:
                record.revoked_at = now
                record.reason = reason

    async def mark_compromised(self, jti: str, reason: str | None = None) -> RefreshTokenRecord | None:
        record = self._records.get(jti)
        if record is None:
            return None

        record.compromised_at = datetime.now(timezone.utc)
        if reason:
            record.reason = reason
        return record
