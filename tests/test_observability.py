import io
import logging

import httpx
import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.application.use_cases.manage_refresh_tokens import RefreshTokenService
from app.core.abuse_prevention import abuse_prevention_service
from app.core.errors import ServiceUnavailableError
from app.core.security import create_refresh_token, decode_token
from app.infrastructure.database.models import Base
from app.infrastructure.repositories.sqlalchemy_refresh_token_repository import SQLAlchemyRefreshTokenRepository
from app.main import app


@pytest.mark.asyncio
async def test_request_id_is_present_in_response():
    image = Image.new("RGB", (8, 8), (255, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/privacy/upload",
            files={"file": ("qa.jpg", buffer.getvalue(), "image/jpeg")},
            headers={"X-Request-ID": "req-test-123"},
        )

    assert response.headers["X-Request-ID"] == "req-test-123"


def test_abuse_logs_do_not_expose_plain_email(caplog):
    abuse_prevention_service.reset()
    with caplog.at_level(logging.WARNING):
        abuse_prevention_service.evaluate_osint_request("ip:1.2.3.4|ua:test", "alpha@example.com")
        abuse_prevention_service.evaluate_osint_request("ip:1.2.3.4|ua:test", "beta@example.com")
        abuse_prevention_service.evaluate_osint_request("ip:1.2.3.4|ua:test", "gamma@example.com")

    output = " ".join(record.message for record in caplog.records)
    assert "example.com" not in output


@pytest.mark.asyncio
async def test_refresh_reuse_attack_is_persisted(tmp_path):
    db_path = tmp_path / "refresh_tokens.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    repository = SQLAlchemyRefreshTokenRepository(sessionmaker(bind=engine))

    old_token = create_refresh_token({"sub": "qa-user"})
    await RefreshTokenService.register_refresh_token(old_token, repository)
    new_token = await RefreshTokenService.rotate_refresh_token(old_token, repository)

    with pytest.raises(ValueError):
        await RefreshTokenService.rotate_refresh_token(old_token, repository)

    old_record = await repository.get_by_jti(decode_token(old_token)["jti"])
    new_record = await repository.get_by_jti(decode_token(new_token)["jti"])

    assert old_record.compromised_at is not None
    assert new_record.revoked_at is not None
    assert new_record.reason == "reuse_attack"


@pytest.mark.asyncio
async def test_osint_returns_503_for_service_unavailable(monkeypatch):
    async def raise_service_unavailable(*args, **kwargs):
        raise ServiceUnavailableError("provider down")

    monkeypatch.setattr("app.presentation.api.endpoints.CheckEmailUseCase.execute", raise_service_unavailable)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/osint/check", json={"email": "qa@example.com"})

    assert response.status_code == 503


def test_future_feature_flags_default_to_disabled():
    from app.core.config import settings

    assert settings.ENABLE_PHONE_LOOKUP is False
    assert settings.ENABLE_VAULT is False
    assert settings.ENABLE_CLEANUP_REPORT is False
    assert settings.ENABLE_DOMAIN_MONITORING is False
