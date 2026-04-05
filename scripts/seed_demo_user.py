from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.core.security import get_password_hash
from app.infrastructure.database.auth_db import get_auth_session_factory
from app.infrastructure.database.models import User


DEMO_EMAIL = "demo@isafe.local"
DEMO_PASSWORD = "DemoPass123!"


def main() -> None:
    session_factory = get_auth_session_factory()

    with session_factory() as session:
        existing = session.execute(select(User).where(User.email == DEMO_EMAIL)).scalar_one_or_none()
        if existing:
            print("demo_user_exists local_demo_credentials_available=true")
            return

        session.add(
            User(
                email=DEMO_EMAIL,
                hashed_password=get_password_hash(DEMO_PASSWORD),
                is_active=True,
            )
        )
        session.commit()

    print("demo_user_created local_demo_credentials_available=true")


if __name__ == "__main__":
    main()
