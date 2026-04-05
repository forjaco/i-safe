import io

import aiosqlite
import httpx
import pytest
from PIL import Image
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.abuse_prevention import abuse_prevention_service
from app.core.security import create_access_token
from app.infrastructure.database.db_config import get_db
from app.main import app


ASYNC_RUNTIME_XFAIL_REASON = (
    "aiosqlite permanece instável no runtime atual do WSL/sandbox. "
    "O problema foi reproduzido fora do pytest em scripts/runtime_async_probe.py."
)


@pytest.fixture(autouse=True)
def clear_overrides():
    previous_hibp_key = settings.HIBP_API_KEY
    previous_mock_flag = settings.EMAIL_CHECK_USE_MOCK
    previous_persist_flag = settings.OSINT_PERSIST_RESULTS
    previous_anonymous_restricted = settings.OSINT_ANONYMOUS_RESTRICTED_MODE
    previous_phone_lookup = settings.ENABLE_PHONE_LOOKUP
    previous_phone_mock = settings.PHONE_LOOKUP_USE_MOCK
    previous_phone_target_max = settings.PHONE_RATE_LIMIT_PER_TARGET_MAX_REQUESTS
    previous_phone_enum_max = settings.PHONE_ENUMERATION_MAX_DISTINCT_TARGETS
    abuse_prevention_service.reset()
    app.dependency_overrides.clear()
    yield
    settings.HIBP_API_KEY = previous_hibp_key
    settings.EMAIL_CHECK_USE_MOCK = previous_mock_flag
    settings.OSINT_PERSIST_RESULTS = previous_persist_flag
    settings.OSINT_ANONYMOUS_RESTRICTED_MODE = previous_anonymous_restricted
    settings.ENABLE_PHONE_LOOKUP = previous_phone_lookup
    settings.PHONE_LOOKUP_USE_MOCK = previous_phone_mock
    settings.PHONE_RATE_LIMIT_PER_TARGET_MAX_REQUESTS = previous_phone_target_max
    settings.PHONE_ENUMERATION_MAX_DISTINCT_TARGETS = previous_phone_enum_max
    abuse_prevention_service.reset()
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.xfail(reason=ASYNC_RUNTIME_XFAIL_REASON, strict=True)
async def test_aiosqlite_connects_and_executes(tmp_path):
    db_path = tmp_path / "aiosqlite_probe.db"

    async def scenario():
        db = await aiosqlite.connect(db_path)
        try:
            await db.execute("create table if not exists probe(id integer primary key, value text)")
            await db.execute("insert into probe(value) values (?)", ("ok",))
            await db.commit()
            cursor = await db.execute("select value from probe")
            rows = await cursor.fetchall()
            assert rows == [("ok",)]
        finally:
            await db.close()

    await asyncio_wait_for(scenario())


@pytest.mark.asyncio
@pytest.mark.xfail(reason=ASYNC_RUNTIME_XFAIL_REASON, strict=True)
async def test_sqlalchemy_async_engine_executes(tmp_path):
    db_path = tmp_path / "sqlalchemy_probe.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)

    async def scenario():
        async with engine.begin() as conn:
            await conn.execute(text("create table if not exists probe(id integer primary key, value text)"))
            await conn.execute(text("insert into probe(value) values ('ok')"))

        async with engine.connect() as conn:
            result = await conn.execute(text("select value from probe"))
            assert result.scalar_one() == "ok"

    try:
        await asyncio_wait_for(scenario())
    finally:
        await engine.dispose()


class FakeSession:
    def __init__(self):
        self.records = []

    def add(self, obj):
        self.records.append(obj)

    async def commit(self):
        return None


@pytest.mark.asyncio
async def test_post_osint_check_returns_mock_response():
    async def override_db():
        yield FakeSession()

    settings.HIBP_API_KEY = None
    settings.EMAIL_CHECK_USE_MOCK = True
    settings.OSINT_PERSIST_RESULTS = True
    app.dependency_overrides[get_db] = override_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/osint/check", json={"email": "qa@example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "MOCK_SUCCESS"
    assert body["is_leaked"] is True
    assert body["sites"] == ["Canva (Mock)", "LinkedIn (2012)"]
    assert body["leaked_data_types"] == ["email", "password"]
    assert body["risk_score"]["pontuacao_total"] >= 100
    assert body["recommendations"]
    assert body["action"] == "[✔] DADOS CRIPTOGRAFADOS E ENGAVETADOS NO AEGIS.DB (MODO MOCK)"


@pytest.mark.asyncio
async def test_post_phone_check_returns_mock_response():
    settings.ENABLE_PHONE_LOOKUP = True
    settings.PHONE_LOOKUP_USE_MOCK = True

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/osint/phone/check", json={"phone": "+5511999999999"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "MOCK_SUCCESS"
    assert body["is_leaked"] is True
    assert body["sites"] == ["Carrier Exposure Dataset (Mock)", "Messaging App Leak (Mock)"]
    assert body["leaked_data_types"] == ["phone", "name"]
    assert body["risk_score"]["pontuacao_total"] >= 50
    assert body["recommendations"]
    assert body["action"] == "[!] CONSULTA DE TELEFONE EM MODO MOCK CONTROLADO"


@pytest.mark.asyncio
async def test_post_phone_check_rejects_invalid_phone():
    settings.ENABLE_PHONE_LOOKUP = True
    settings.PHONE_LOOKUP_USE_MOCK = True

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/osint/phone/check", json={"phone": "11999999999"})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_phone_check_returns_503_when_feature_disabled():
    settings.ENABLE_PHONE_LOOKUP = False

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/osint/phone/check", json={"phone": "+5511999999999"})

    assert response.status_code == 503
    assert response.json()["detail"] == "Serviço indisponível no momento."


@pytest.mark.asyncio
async def test_post_phone_check_returns_restricted_response_for_anonymous_request():
    settings.ENABLE_PHONE_LOOKUP = True
    settings.PHONE_LOOKUP_USE_MOCK = True
    settings.OSINT_ANONYMOUS_RESTRICTED_MODE = True

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/osint/phone/check", json={"phone": "+5511999999999"})

    assert response.status_code == 200
    assert response.json()["status"] == "RESTRICTED"


@pytest.mark.asyncio
async def test_post_phone_check_rate_limits_by_target():
    settings.ENABLE_PHONE_LOOKUP = True
    settings.PHONE_LOOKUP_USE_MOCK = True
    settings.PHONE_RATE_LIMIT_PER_TARGET_MAX_REQUESTS = 2

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post("/api/v1/osint/phone/check", json={"phone": "+5511999999999"})
        await client.post("/api/v1/osint/phone/check", json={"phone": "+5511999999999"})
        response = await client.post("/api/v1/osint/phone/check", json={"phone": "+5511999999999"})

    assert response.status_code == 429
    assert response.headers["Retry-After"] == str(settings.PHONE_RATE_LIMIT_PER_TARGET_WINDOW_SECONDS)
    assert response.json()["status"] == "RESTRICTED"


@pytest.mark.asyncio
async def test_post_privacy_upload_returns_scan_result():
    image = Image.new("RGB", (8, 8), (255, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/privacy/upload",
            files={"file": ("qa.jpg", buffer.getvalue(), "image/jpeg")},
        )

    assert response.status_code == 200
    assert response.json() == {
        "filename": "qa.jpg",
        "is_safe": True,
        "privacy_alerts": [],
        "size_bytes": len(buffer.getvalue()),
        "metadata_found": False,
        "sanitization_available": False,
    }


@pytest.mark.asyncio
async def test_post_osint_check_returns_restricted_response_for_enumeration_pattern():
    async def override_db():
        yield FakeSession()

    settings.HIBP_API_KEY = None
    settings.EMAIL_CHECK_USE_MOCK = True
    settings.OSINT_ENUMERATION_MAX_DISTINCT_TARGETS = 2
    settings.OSINT_PERSIST_RESULTS = True
    app.dependency_overrides[get_db] = override_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post("/api/v1/osint/check", json={"email": "alpha@example.com"})
        await client.post("/api/v1/osint/check", json={"email": "beta@example.com"})
        response = await client.post("/api/v1/osint/check", json={"email": "gamma@example.com"})

    assert response.status_code == 200
    assert response.json()["status"] == "RESTRICTED"
    assert response.json()["sites"] == []


@pytest.mark.asyncio
async def test_post_osint_check_rate_limits_by_target():
    async def override_db():
        yield FakeSession()

    settings.HIBP_API_KEY = None
    settings.EMAIL_CHECK_USE_MOCK = True
    settings.OSINT_RATE_LIMIT_PER_TARGET_MAX_REQUESTS = 2
    settings.OSINT_PERSIST_RESULTS = True
    app.dependency_overrides[get_db] = override_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await client.post("/api/v1/osint/check", json={"email": "same@example.com"})
        await client.post("/api/v1/osint/check", json={"email": "same@example.com"})
        response = await client.post("/api/v1/osint/check", json={"email": "same@example.com"})

    assert response.status_code == 429
    assert response.headers["Retry-After"] == str(settings.OSINT_RATE_LIMIT_PER_TARGET_WINDOW_SECONDS)
    assert response.json()["status"] == "RESTRICTED"


@pytest.mark.asyncio
async def test_post_osint_check_can_be_restricted_for_anonymous_requests():
    async def override_db():
        yield FakeSession()

    settings.HIBP_API_KEY = None
    settings.EMAIL_CHECK_USE_MOCK = True
    settings.OSINT_ANONYMOUS_RESTRICTED_MODE = True
    settings.OSINT_PERSIST_RESULTS = True
    app.dependency_overrides[get_db] = override_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/osint/check", json={"email": "qa@example.com"})

    assert response.status_code == 200
    assert response.json()["status"] == "RESTRICTED"


@pytest.mark.asyncio
async def test_post_osint_check_returns_full_response_for_authenticated_request():
    async def override_db():
        yield FakeSession()

    settings.HIBP_API_KEY = None
    settings.EMAIL_CHECK_USE_MOCK = True
    settings.OSINT_ANONYMOUS_RESTRICTED_MODE = True
    settings.OSINT_PERSIST_RESULTS = True
    app.dependency_overrides[get_db] = override_db
    access_token = create_access_token({"sub": "qa@example.com"})

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/osint/check",
            json={"email": "qa@example.com"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "MOCK_SUCCESS"


@pytest.mark.asyncio
async def test_post_phone_check_returns_full_response_for_authenticated_request():
    settings.ENABLE_PHONE_LOOKUP = True
    settings.PHONE_LOOKUP_USE_MOCK = True
    settings.OSINT_ANONYMOUS_RESTRICTED_MODE = True
    access_token = create_access_token({"sub": "qa@example.com"})

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/osint/phone/check",
            json={"phone": "+5511999999999"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "MOCK_SUCCESS"


async def asyncio_wait_for(awaitable, timeout=2.0):
    import asyncio

    try:
        return await asyncio.wait_for(awaitable, timeout=timeout)
    except TimeoutError as exc:
        pytest.fail(
            f"Operação async excedeu {timeout}s. Isso indica problema de ambiente, dependência ou configuração async, não uma falha de asserção do teste."
        )
