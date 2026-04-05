import pytest

from app.core.config import Settings


def test_settings_parse_origins_and_image_types():
    settings = Settings(
        ENCRYPTION_KEY="fc8fdfbaeb33979eaee91d84b2efc8f38d17ee6a6eb7bc3faad4dd15d742fb62",
        ALLOWED_ORIGINS="http://localhost:3000, http://localhost:5173",
        IMAGE_ALLOWED_MIME_TYPES="image/jpeg,image/png",
    )

    assert settings.get_cors_origins == ["http://localhost:3000", "http://localhost:5173"]
    assert settings.image_allowed_mime_types == ["image/jpeg", "image/png"]


def test_settings_reject_invalid_encryption_key():
    with pytest.raises(ValueError):
        Settings(ENCRYPTION_KEY="abc")


def test_settings_normalize_placeholder_hibp_key():
    settings = Settings(
        ENCRYPTION_KEY="fc8fdfbaeb33979eaee91d84b2efc8f38d17ee6a6eb7bc3faad4dd15d742fb62",
        HIBP_API_KEY="insira_seu_token_aqui",
    )

    assert settings.HIBP_API_KEY is None


def test_settings_reject_wildcard_origin_in_production():
    with pytest.raises(ValueError):
        Settings(
            ENCRYPTION_KEY="fc8fdfbaeb33979eaee91d84b2efc8f38d17ee6a6eb7bc3faad4dd15d742fb62",
            ENVIRONMENT="production",
            ALLOWED_ORIGINS="*",
        )


def test_settings_reject_wildcard_host_in_production():
    with pytest.raises(ValueError):
        Settings(
            ENCRYPTION_KEY="fc8fdfbaeb33979eaee91d84b2efc8f38d17ee6a6eb7bc3faad4dd15d742fb62",
            ENVIRONMENT="production",
            ALLOWED_HOSTS="*",
        )


def test_settings_promote_postgres_url_for_async_and_auth_paths():
    settings = Settings(
        ENCRYPTION_KEY="fc8fdfbaeb33979eaee91d84b2efc8f38d17ee6a6eb7bc3faad4dd15d742fb62",
        ENVIRONMENT="production",
        PRODUCTION_DATABASE_URL="postgresql://user:pass@db:5432/isafe",
        AUTH_COOKIE_SECURE=True,
    )

    assert settings.effective_async_database_url == "postgresql+asyncpg://user:pass@db:5432/isafe"
    assert settings.effective_auth_database_url == "postgresql+psycopg://user:pass@db:5432/isafe"


def test_settings_require_secure_auth_cookie_in_production():
    with pytest.raises(ValueError):
        Settings(
            ENCRYPTION_KEY="fc8fdfbaeb33979eaee91d84b2efc8f38d17ee6a6eb7bc3faad4dd15d742fb62",
            ENVIRONMENT="production",
            AUTH_COOKIE_SECURE=False,
        )


def test_refresh_header_fallback_defaults_to_disabled_in_production():
    settings = Settings(
        ENCRYPTION_KEY="fc8fdfbaeb33979eaee91d84b2efc8f38d17ee6a6eb7bc3faad4dd15d742fb62",
        ENVIRONMENT="production",
        AUTH_COOKIE_SECURE=True,
    )

    assert settings.effective_refresh_header_fallback is False


def test_phone_lookup_defaults_to_disabled_and_mock_ready():
    settings = Settings(
        ENCRYPTION_KEY="fc8fdfbaeb33979eaee91d84b2efc8f38d17ee6a6eb7bc3faad4dd15d742fb62",
    )

    assert settings.ENABLE_PHONE_LOOKUP is False
    assert settings.PHONE_LOOKUP_USE_MOCK is True
