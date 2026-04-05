import io

import httpx
import pytest
from PIL import Image

from app.core.config import settings
from app.core.errors import PersistenceUnavailableError, ServiceUnavailableError
from app.main import app


def build_image_bytes(size=(16, 16), fmt="JPEG") -> bytes:
    image = Image.new("RGB", size, (255, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_healthcheck_returns_ok():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_readiness_returns_ready():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_invalid_host_is_rejected():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://evil.invalid") as client:
        response = await client.get("/health")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_payload_too_large_returns_413(monkeypatch):
    monkeypatch.setattr("app.core.http_middleware.settings.HTTP_MAX_REQUEST_SIZE_BYTES", 10)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/osint/check",
            json={"email": "qa@example.com"},
            headers={"Content-Length": "999"},
        )

    assert response.status_code == 413
    assert response.json()["detail"] == "Payload excede o limite de segurança permitido."


@pytest.mark.asyncio
async def test_osint_returns_503_for_provider_timeout(monkeypatch):
    async def raise_timeout(*args, **kwargs):
        raise ServiceUnavailableError("timeout")

    monkeypatch.setattr("app.presentation.api.endpoints.CheckEmailUseCase.execute", raise_timeout)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/osint/check", json={"email": "qa@example.com"})

    assert response.status_code == 503
    assert response.json()["detail"] == "Serviço indisponível no momento."


@pytest.mark.asyncio
async def test_phone_lookup_returns_503_when_provider_is_not_configured():
    previous_phone_lookup = settings.ENABLE_PHONE_LOOKUP
    previous_phone_mock = settings.PHONE_LOOKUP_USE_MOCK
    settings.ENABLE_PHONE_LOOKUP = True
    settings.PHONE_LOOKUP_USE_MOCK = False

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/osint/phone/check", json={"phone": "+5511999999999"})

    settings.ENABLE_PHONE_LOOKUP = previous_phone_lookup
    settings.PHONE_LOOKUP_USE_MOCK = previous_phone_mock

    assert response.status_code == 503
    assert response.json()["detail"] == "Serviço indisponível no momento."


@pytest.mark.asyncio
async def test_readiness_returns_503_when_auth_storage_unavailable(monkeypatch):
    def raise_unavailable():
        raise PersistenceUnavailableError("down")

    monkeypatch.setattr("app.main.get_auth_session_factory", raise_unavailable)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"


@pytest.mark.asyncio
async def test_upload_route_rejects_oversized_payload(monkeypatch):
    monkeypatch.setattr("app.application.use_cases.image_analyzer.settings.IMAGE_MAX_FILE_SIZE_BYTES", 10)
    file_bytes = build_image_bytes()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/privacy/upload",
            files={"file": ("big.jpg", file_bytes, "image/jpeg")},
        )

    assert response.status_code == 400
    assert "limite de segurança" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_route_rejects_excessive_resolution(monkeypatch):
    monkeypatch.setattr("app.application.use_cases.image_analyzer.settings.IMAGE_MAX_PIXELS", 100)
    file_bytes = build_image_bytes(size=(16, 16))

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/privacy/upload",
            files={"file": ("huge.jpg", file_bytes, "image/jpeg")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "A imagem excede o limite seguro de resolução."
