from datetime import timedelta

from jose import jwt
import pytest

from app.application.entities.refresh_token import RefreshTokenRecord
from app.application.use_cases.manage_refresh_tokens import RefreshTokenService
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    decrypt_sensitive_data,
    encrypt_sensitive_data,
    get_password_hash,
    validate_refresh_token,
    verify_password,
)
from app.infrastructure.repositories.in_memory_refresh_token_repository import InMemoryRefreshTokenRepository


def test_encrypt_and_decrypt_sensitive_data_round_trip():
    payload = "qa@i-safe.local"
    encrypted = encrypt_sensitive_data(payload)

    assert ":" in encrypted
    assert decrypt_sensitive_data(encrypted) == payload


def test_password_hash_uses_argon2_and_verifies():
    hashed = get_password_hash("senha-segura-123")

    assert hashed.startswith("$argon2")
    assert verify_password("senha-segura-123", hashed) is True


def test_create_access_token_encodes_subject():
    token = create_access_token({"sub": "qa-user"})
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert decoded["sub"] == "qa-user"


def test_create_refresh_token_marks_refresh_type():
    token = create_refresh_token({"sub": "qa-user"})
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert decoded["sub"] == "qa-user"
    assert decoded["type"] == "refresh"
    assert decoded["jti"]


def test_aes_gcm_tamper_detection_fails_closed():
    encrypted = encrypt_sensitive_data("sensitive")
    nonce_hex, ct_hex = encrypted.split(":")
    tampered_payload = f"{nonce_hex}:{ct_hex[:-2]}00"

    try:
        decrypt_sensitive_data(tampered_payload)
        assert False, "tampered payload should not decrypt"
    except ValueError:
        assert True


def test_validate_refresh_token_rejects_token_without_refresh_type():
    token = create_access_token({"sub": "qa-user"})

    try:
        validate_refresh_token(token)
        assert False, "access token must not validate as refresh token"
    except ValueError:
        assert True


def test_validate_refresh_token_accepts_valid_refresh_token():
    token = create_refresh_token({"sub": "qa-user"})
    claims = validate_refresh_token(token)

    assert claims["sub"] == "qa-user"
    assert claims["type"] == "refresh"
    assert claims["jti"]


def test_decode_token_rejects_malformed_token():
    try:
        decode_token("invalid.token.value")
        assert False, "malformed token must be rejected"
    except ValueError:
        assert True


def test_validate_refresh_token_rejects_revoked_by_checker():
    token = create_refresh_token({"sub": "qa-user"})
    claims = decode_token(token)

    with pytest.raises(ValueError):
        validate_refresh_token(token, revocation_checker=lambda jti: jti == claims["jti"])


@pytest.mark.asyncio
async def test_refresh_service_accepts_valid_not_revoked_token():
    repository = InMemoryRefreshTokenRepository()
    token = create_refresh_token({"sub": "qa-user"})
    await RefreshTokenService.register_refresh_token(token, repository)

    claims = await RefreshTokenService.validate_refresh_token_not_revoked(token, repository)

    assert claims["sub"] == "qa-user"


@pytest.mark.asyncio
async def test_refresh_service_rejects_revoked_token():
    repository = InMemoryRefreshTokenRepository()
    token = create_refresh_token({"sub": "qa-user"})
    claims = decode_token(token)
    await RefreshTokenService.register_refresh_token(token, repository)
    await RefreshTokenService.revoke_refresh_token_by_jti(claims["jti"], repository, reason="logout")

    with pytest.raises(ValueError):
        await RefreshTokenService.validate_refresh_token_not_revoked(token, repository)


@pytest.mark.asyncio
async def test_refresh_service_rejects_expired_token_record():
    repository = InMemoryRefreshTokenRepository()
    token = create_refresh_token({"sub": "qa-user"})
    claims = decode_token(token)
    expired_record = RefreshTokenRecord(
        jti=claims["jti"],
        sub=claims["sub"],
        token_type=claims["type"],
        issued_at=RefreshTokenService._parse_timestamp(claims["iat"]),
        expires_at=RefreshTokenService._parse_timestamp(claims["iat"]) - timedelta(seconds=1),
    )
    await repository.save(expired_record)

    with pytest.raises(ValueError):
        await RefreshTokenService.validate_refresh_token_not_revoked(token, repository)


def test_validate_refresh_token_rejects_expired_token():
    token = create_refresh_token({"sub": "qa-user"}, expires_delta=timedelta(seconds=-1))

    with pytest.raises(ValueError):
        validate_refresh_token(token)


def test_validate_refresh_token_rejects_refresh_without_jti():
    token = jwt.encode(
        {"sub": "qa-user", "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    with pytest.raises(ValueError):
        validate_refresh_token(token)


@pytest.mark.asyncio
async def test_rotate_refresh_token_rotates_and_revokes_previous():
    repository = InMemoryRefreshTokenRepository()
    old_token = create_refresh_token({"sub": "qa-user"})
    await RefreshTokenService.register_refresh_token(old_token, repository)
    old_claims = decode_token(old_token)

    new_token = await RefreshTokenService.rotate_refresh_token(old_token, repository)
    new_claims = decode_token(new_token)
    old_record = await repository.get_by_jti(old_claims["jti"])
    new_record = await repository.get_by_jti(new_claims["jti"])

    assert old_record.revoked_at is not None
    assert old_record.reason == "rotated"
    assert new_claims["parent_jti"] == old_claims["jti"]
    assert new_record.parent_jti == old_claims["jti"]


@pytest.mark.asyncio
async def test_rotated_old_refresh_token_is_rejected():
    repository = InMemoryRefreshTokenRepository()
    old_token = create_refresh_token({"sub": "qa-user"})
    await RefreshTokenService.register_refresh_token(old_token, repository)
    await RefreshTokenService.rotate_refresh_token(old_token, repository)

    with pytest.raises(ValueError):
        await RefreshTokenService.validate_refresh_token_not_revoked(old_token, repository)


@pytest.mark.asyncio
async def test_reuse_attack_is_detected_and_revokes_active_chain():
    repository = InMemoryRefreshTokenRepository()
    old_token = create_refresh_token({"sub": "qa-user"})
    await RefreshTokenService.register_refresh_token(old_token, repository)

    new_token = await RefreshTokenService.rotate_refresh_token(old_token, repository)
    old_claims = decode_token(old_token)
    new_claims = decode_token(new_token)

    with pytest.raises(ValueError):
        await RefreshTokenService.rotate_refresh_token(old_token, repository)

    old_record = await repository.get_by_jti(old_claims["jti"])
    new_record = await repository.get_by_jti(new_claims["jti"])

    assert old_record.compromised_at is not None
    assert old_record.reason == "reuse_attack"
    assert new_record.revoked_at is not None
    assert new_record.reason == "reuse_attack"
