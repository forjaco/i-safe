from functools import lru_cache
from threading import Lock

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.errors import PersistenceUnavailableError
from app.infrastructure.database.models import Base


_init_lock = Lock()
_initialized = False


def _derive_auth_database_url() -> str:
    return settings.effective_auth_database_url


@lru_cache(maxsize=1)
def get_auth_engine() -> Engine:
    try:
        database_url = _derive_auth_database_url()
        engine_kwargs = {"echo": settings.DATABASE_ECHO, "future": True}
        if database_url.startswith("sqlite:///"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        return create_engine(database_url, **engine_kwargs)
    except Exception as exc:
        raise PersistenceUnavailableError("Storage de autenticação indisponível.") from exc


@lru_cache(maxsize=1)
def get_auth_session_factory() -> sessionmaker[Session]:
    engine = get_auth_engine()
    _ensure_auth_tables(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _ensure_auth_tables(engine: Engine) -> None:
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        try:
            Base.metadata.create_all(engine)
        except Exception as exc:
            raise PersistenceUnavailableError("Não foi possível inicializar o storage de autenticação.") from exc
        _initialized = True
