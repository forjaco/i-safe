from typing import Protocol

from app.application.entities.user import UserRecord


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> UserRecord | None: ...

    async def get_by_id(self, user_id: int) -> UserRecord | None: ...
