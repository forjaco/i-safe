import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.abuse_prevention import abuse_prevention_service
from app.core.security import create_refresh_token, decode_token, get_password_hash
from app.infrastructure.database.models import Base, User
from app.infrastructure.repositories.sqlalchemy_refresh_token_repository import SQLAlchemyRefreshTokenRepository
from app.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.main import app
from app.presentation.api.auth import get_refresh_token_repository, get_user_repository


@pytest.fixture
def auth_repositories(tmp_path):
    previous_login_ip_max = settings.AUTH_RATE_LIMIT_PER_IP_MAX_REQUESTS
    previous_login_identifier_max = settings.AUTH_LOGIN_RATE_LIMIT_PER_IDENTIFIER_MAX_REQUESTS
    previous_refresh_ip_max = settings.AUTH_REFRESH_RATE_LIMIT_PER_IP_MAX_REQUESTS
    previous_logout_ip_max = settings.AUTH_LOGOUT_RATE_LIMIT_PER_IP_MAX_REQUESTS
    previous_refresh_header_fallback = settings.ENABLE_REFRESH_HEADER_FALLBACK
    abuse_prevention_service.reset()
    db_path = tmp_path / "auth.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        session.add(
            User(
                email="qa@example.com",
                hashed_password=get_password_hash("senha-segura-123"),
                is_active=True,
            )
        )
        session.commit()

    user_repository = SQLAlchemyUserRepository(session_factory)
    refresh_repository = SQLAlchemyRefreshTokenRepository(session_factory)

    async def override_user_repository():
        return user_repository

    async def override_refresh_repository():
        return refresh_repository

    app.dependency_overrides[get_user_repository] = override_user_repository
    app.dependency_overrides[get_refresh_token_repository] = override_refresh_repository
    try:
        yield user_repository, refresh_repository
    finally:
        settings.AUTH_RATE_LIMIT_PER_IP_MAX_REQUESTS = previous_login_ip_max
        settings.AUTH_LOGIN_RATE_LIMIT_PER_IDENTIFIER_MAX_REQUESTS = previous_login_identifier_max
        settings.AUTH_REFRESH_RATE_LIMIT_PER_IP_MAX_REQUESTS = previous_refresh_ip_max
        settings.AUTH_LOGOUT_RATE_LIMIT_PER_IP_MAX_REQUESTS = previous_logout_ip_max
        settings.ENABLE_REFRESH_HEADER_FALLBACK = previous_refresh_header_fallback
        abuse_prevention_service.reset()
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.mark.asyncio
async def test_login_valid_returns_access_token_and_sets_refresh_cookie(auth_repositories):
    _, refresh_repository = auth_repositories

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "qa@example.com", "password": "senha-segura-123"},
        )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
    refresh_token = response.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    assert refresh_token

    refresh_claims = decode_token(refresh_token)
    stored_record = await refresh_repository.get_by_jti(refresh_claims["jti"])
    assert stored_record is not None
    assert stored_record.sub == "qa@example.com"


@pytest.mark.asyncio
async def test_me_returns_authenticated_user_for_valid_bearer(auth_repositories):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "qa@example.com", "password": "senha-segura-123"},
        )
        access_token = login_response.json()["access_token"]
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert me_response.status_code == 200
    assert me_response.json() == {
        "id": 1,
        "email": "qa@example.com",
        "is_active": True,
    }


@pytest.mark.asyncio
async def test_login_invalid_rejects_credentials(auth_repositories):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "qa@example.com", "password": "senha-errada-123"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas."


@pytest.mark.asyncio
async def test_me_rejects_missing_access_token(auth_repositories):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Access token inválido."


@pytest.mark.asyncio
async def test_me_rejects_refresh_token_as_bearer(auth_repositories):
    refresh_token = create_refresh_token({"sub": "qa@example.com"})

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Access token inválido."


@pytest.mark.asyncio
async def test_refresh_valid_rotates_token_and_issues_new_access(auth_repositories):
    _, refresh_repository = auth_repositories

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "qa@example.com", "password": "senha-segura-123"},
        )
        old_refresh = login_response.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)

        refresh_response = await client.post("/api/v1/auth/refresh")
        new_refresh = refresh_response.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
        new_access_token = refresh_response.json()["access_token"]
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )

    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"]
    assert me_response.status_code == 200
    assert new_refresh
    assert new_refresh != old_refresh

    old_record = await refresh_repository.get_by_jti(decode_token(old_refresh)["jti"])
    new_record = await refresh_repository.get_by_jti(decode_token(new_refresh)["jti"])
    assert old_record.revoked_at is not None
    assert old_record.reason == "rotated"
    assert new_record.parent_jti == old_record.jti


@pytest.mark.asyncio
async def test_refresh_old_token_rejected_and_reuse_attack_detected(auth_repositories):
    _, refresh_repository = auth_repositories

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "qa@example.com", "password": "senha-segura-123"},
        )
        old_refresh = login_response.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)

        refresh_response = await client.post("/api/v1/auth/refresh")
        new_refresh = refresh_response.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)

        client.cookies.clear()
        reused_response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {old_refresh}"},
        )

    assert reused_response.status_code == 401
    assert reused_response.json()["detail"] == "Sessão inválida. Faça login novamente."

    old_record = await refresh_repository.get_by_jti(decode_token(old_refresh)["jti"])
    new_record = await refresh_repository.get_by_jti(decode_token(new_refresh)["jti"])
    assert old_record.compromised_at is not None
    assert old_record.reason == "reuse_attack"
    assert new_record.revoked_at is not None
    assert new_record.reason == "reuse_attack"


@pytest.mark.asyncio
async def test_logout_revokes_current_refresh_token(auth_repositories):
    _, refresh_repository = auth_repositories

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "qa@example.com", "password": "senha-segura-123"},
        )
        refresh_token = login_response.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)

        logout_response = await client.post("/api/v1/auth/logout")

    assert logout_response.status_code == 200
    assert logout_response.json() == {"status": "logged_out"}
    assert f"{settings.AUTH_REFRESH_COOKIE_NAME}=\"\"" in logout_response.headers["set-cookie"]

    stored_record = await refresh_repository.get_by_jti(decode_token(refresh_token)["jti"])
    assert stored_record.revoked_at is not None
    assert stored_record.reason == "logout"


@pytest.mark.asyncio
async def test_refresh_revoked_token_is_rejected_after_logout(auth_repositories):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post(
            "/api/v1/auth/login",
            json={"email": "qa@example.com", "password": "senha-segura-123"},
        )
        await client.post("/api/v1/auth/logout")
        response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token inválido."


@pytest.mark.asyncio
async def test_login_is_rate_limited_after_multiple_failures(auth_repositories):
    settings.AUTH_LOGIN_RATE_LIMIT_PER_IDENTIFIER_MAX_REQUESTS = 2

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post("/api/v1/auth/login", json={"email": "qa@example.com", "password": "senha-errada-123"})
        await client.post("/api/v1/auth/login", json={"email": "qa@example.com", "password": "senha-errada-123"})
        response = await client.post("/api/v1/auth/login", json={"email": "qa@example.com", "password": "senha-errada-123"})

    assert response.status_code == 429
    assert response.headers["Retry-After"] == str(settings.AUTH_LOGIN_RATE_LIMIT_PER_IDENTIFIER_WINDOW_SECONDS)


@pytest.mark.asyncio
async def test_refresh_is_rate_limited(auth_repositories):
    settings.AUTH_REFRESH_RATE_LIMIT_PER_IP_MAX_REQUESTS = 1

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post(
            "/api/v1/auth/login",
            json={"email": "qa@example.com", "password": "senha-segura-123"},
        )
        await client.post("/api/v1/auth/refresh")
        response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 429
    assert response.headers["Retry-After"] == str(settings.AUTH_REFRESH_RATE_LIMIT_PER_IP_WINDOW_SECONDS)


@pytest.mark.asyncio
async def test_refresh_header_fallback_can_be_blocked(auth_repositories):
    settings.ENABLE_REFRESH_HEADER_FALLBACK = False
    refresh_token = create_refresh_token({"sub": "qa@example.com"})

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token inválido."


@pytest.mark.asyncio
async def test_logout_is_rate_limited(auth_repositories):
    settings.AUTH_LOGOUT_RATE_LIMIT_PER_IP_MAX_REQUESTS = 1

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post(
            "/api/v1/auth/login",
            json={"email": "qa@example.com", "password": "senha-segura-123"},
        )
        await client.post("/api/v1/auth/logout")
        response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 429
    assert response.headers["Retry-After"] == str(settings.AUTH_LOGOUT_RATE_LIMIT_PER_IP_WINDOW_SECONDS)
