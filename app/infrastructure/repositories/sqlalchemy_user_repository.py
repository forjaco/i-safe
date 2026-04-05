from sqlalchemy.orm import Session, sessionmaker

from app.application.entities.user import UserRecord
from app.infrastructure.database.models import User


class SQLAlchemyUserRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    async def get_by_email(self, email: str) -> UserRecord | None:
        normalized = email.strip().lower()
        with self._session_factory() as session:
            model = session.query(User).filter(User.email == normalized).one_or_none()
            if model is None:
                return None
            return UserRecord(
                id=model.id,
                email=model.email,
                hashed_password=model.hashed_password,
                is_active=model.is_active,
            )

    async def get_by_id(self, user_id: int) -> UserRecord | None:
        with self._session_factory() as session:
            model = session.get(User, user_id)
            if model is None:
                return None
            return UserRecord(
                id=model.id,
                email=model.email,
                hashed_password=model.hashed_password,
                is_active=model.is_active,
            )
