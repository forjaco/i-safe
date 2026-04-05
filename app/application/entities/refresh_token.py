from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class RefreshTokenRecord:
    jti: str
    sub: str
    token_type: str
    issued_at: datetime
    expires_at: datetime
    parent_jti: str | None = None
    revoked_at: datetime | None = None
    compromised_at: datetime | None = None
    reason: str | None = None
