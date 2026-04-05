import re
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Configuração central do I-safe.
    Mantém a aplicação local-first com SQLite por padrão e permite evolução
    para backends assíncronos compatíveis via DATABASE_URL.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = Field(default="I-safe")
    ENVIRONMENT: str = Field(default="development")
    ALLOWED_HOSTS: str = Field(default="localhost,127.0.0.1,testserver")

    SECRET_KEY: str = Field(default="CHAVE_EMERGENCIA_MOCK_NAO_USE_EM_PROD")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    ALLOWED_ORIGINS: str = Field(default="http://localhost")
    HIBP_API_KEY: str | None = None
    HIBP_TIMEOUT_SECONDS: float = Field(default=10.0, gt=0)
    HIBP_MAX_RETRIES: int = Field(default=1, ge=0, le=3)
    HIBP_RETRY_BACKOFF_SECONDS: float = Field(default=0.2, ge=0, le=2.0)
    EMAIL_CHECK_USE_MOCK: bool = Field(default=True)
    OSINT_PERSIST_RESULTS: bool = Field(default=True)
    PHONE_LOOKUP_USE_MOCK: bool = Field(default=True)

    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./aegis.db")
    DATABASE_ECHO: bool = Field(default=False)
    PRODUCTION_DATABASE_URL: str | None = None
    AUTH_DATABASE_URL: str | None = None

    IMAGE_MAX_FILE_SIZE_BYTES: int = Field(default=5 * 1024 * 1024, gt=0)
    IMAGE_MAX_PIXELS: int = Field(default=20_000_000, gt=0)
    IMAGE_ALLOWED_MIME_TYPES: str = Field(default="image/jpeg,image/png")
    HTTP_MAX_REQUEST_SIZE_BYTES: int = Field(default=6 * 1024 * 1024, gt=0)
    OSINT_RATE_LIMIT_PER_IP_WINDOW_SECONDS: int = Field(default=60, gt=0)
    OSINT_RATE_LIMIT_PER_IP_MAX_REQUESTS: int = Field(default=10, gt=0)
    OSINT_RATE_LIMIT_PER_TARGET_WINDOW_SECONDS: int = Field(default=300, gt=0)
    OSINT_RATE_LIMIT_PER_TARGET_MAX_REQUESTS: int = Field(default=5, gt=0)
    OSINT_ENUMERATION_WINDOW_SECONDS: int = Field(default=120, gt=0)
    OSINT_ENUMERATION_MAX_DISTINCT_TARGETS: int = Field(default=5, gt=0)
    OSINT_ANONYMOUS_RESTRICTED_MODE: bool = Field(default=False)
    ENABLE_PHONE_LOOKUP: bool = Field(default=False)
    PHONE_RATE_LIMIT_PER_IP_WINDOW_SECONDS: int = Field(default=60, gt=0)
    PHONE_RATE_LIMIT_PER_IP_MAX_REQUESTS: int = Field(default=10, gt=0)
    PHONE_RATE_LIMIT_PER_TARGET_WINDOW_SECONDS: int = Field(default=300, gt=0)
    PHONE_RATE_LIMIT_PER_TARGET_MAX_REQUESTS: int = Field(default=5, gt=0)
    PHONE_ENUMERATION_WINDOW_SECONDS: int = Field(default=120, gt=0)
    PHONE_ENUMERATION_MAX_DISTINCT_TARGETS: int = Field(default=5, gt=0)
    ENABLE_VAULT: bool = Field(default=False)
    ENABLE_CLEANUP_REPORT: bool = Field(default=False)
    ENABLE_DOMAIN_MONITORING: bool = Field(default=False)
    AUTH_REFRESH_COOKIE_NAME: str = Field(default="isafe_refresh_token")
    AUTH_COOKIE_SECURE: bool = Field(default=False)
    AUTH_COOKIE_SAMESITE: str = Field(default="lax")
    AUTH_COOKIE_PATH: str = Field(default="/api/v1/auth")
    ENABLE_REFRESH_HEADER_FALLBACK: bool | None = Field(default=None)
    AUTH_RATE_LIMIT_PER_IP_WINDOW_SECONDS: int = Field(default=60, gt=0)
    AUTH_RATE_LIMIT_PER_IP_MAX_REQUESTS: int = Field(default=20, gt=0)
    AUTH_LOGIN_RATE_LIMIT_PER_IDENTIFIER_WINDOW_SECONDS: int = Field(default=300, gt=0)
    AUTH_LOGIN_RATE_LIMIT_PER_IDENTIFIER_MAX_REQUESTS: int = Field(default=5, gt=0)
    AUTH_REFRESH_RATE_LIMIT_PER_IP_WINDOW_SECONDS: int = Field(default=60, gt=0)
    AUTH_REFRESH_RATE_LIMIT_PER_IP_MAX_REQUESTS: int = Field(default=10, gt=0)
    AUTH_LOGOUT_RATE_LIMIT_PER_IP_WINDOW_SECONDS: int = Field(default=60, gt=0)
    AUTH_LOGOUT_RATE_LIMIT_PER_IP_MAX_REQUESTS: int = Field(default=20, gt=0)

    @property
    def get_cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def trusted_hosts(self) -> List[str]:
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

    @property
    def image_allowed_mime_types(self) -> List[str]:
        return [item.strip() for item in self.IMAGE_ALLOWED_MIME_TYPES.split(",") if item.strip()]

    @property
    def effective_async_database_url(self) -> str:
        source_url = self.PRODUCTION_DATABASE_URL if self.ENVIRONMENT == "production" and self.PRODUCTION_DATABASE_URL else self.DATABASE_URL
        if source_url.startswith("postgresql://"):
            return source_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return source_url

    @property
    def effective_auth_database_url(self) -> str:
        if self.AUTH_DATABASE_URL:
            return self.AUTH_DATABASE_URL

        source_url = self.effective_async_database_url
        if source_url.startswith("sqlite+aiosqlite:///"):
            return source_url.replace("sqlite+aiosqlite:///", "sqlite:///", 1)
        if source_url.startswith("sqlite+aiosqlite://"):
            return source_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        if source_url.startswith("postgresql+asyncpg://"):
            return source_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        if source_url.startswith("postgresql://"):
            return source_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return source_url

    @property
    def effective_refresh_header_fallback(self) -> bool:
        if self.ENABLE_REFRESH_HEADER_FALLBACK is not None:
            return self.ENABLE_REFRESH_HEADER_FALLBACK
        return self.ENVIRONMENT != "production"

    ENCRYPTION_KEY: str

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        v = v.strip()

        if not v or len(v) != 64:
            raise ValueError(
                f"[Critical Error] A ENCRYPTION_KEY inserida não atende à métrica governamental! "
                f"Possui {len(v)} caracteres. Deve conter exatamente 64 (32 bytes)."
            )

        if not re.fullmatch(r"[0-9a-fA-F]+", v):
            raise ValueError(
                "[Critical Error] A sua ENCRYPTION_KEY está contaminada. Deve conter APENAS cadeias hexadecimais (0-9 e a-f)."
            )

        return v

    @field_validator("HIBP_API_KEY", mode="before")
    @classmethod
    def normalize_hibp_api_key(cls, v: str | None) -> str | None:
        if v is None:
            return None

        v = str(v).strip()
        if not v or v.lower() in {"insira_seu_token_aqui", "changeme", "your_api_key_here"}:
            return None

        return v

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_allowed_origins(cls, v: str, info) -> str:
        environment = info.data.get("ENVIRONMENT", "development")
        origins = [origin.strip() for origin in str(v).split(",") if origin.strip()]
        if environment == "production" and "*" in origins:
            raise ValueError("ALLOWED_ORIGINS não pode conter wildcard em produção.")
        return ",".join(origins)

    @field_validator("ALLOWED_HOSTS")
    @classmethod
    def validate_allowed_hosts(cls, v: str, info) -> str:
        environment = info.data.get("ENVIRONMENT", "development")
        hosts = [host.strip() for host in str(v).split(",") if host.strip()]
        if environment == "production" and "*" in hosts:
            raise ValueError("ALLOWED_HOSTS não pode conter wildcard em produção.")
        return ",".join(hosts)

    @field_validator("PRODUCTION_DATABASE_URL")
    @classmethod
    def validate_production_database_url(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) and v.strip() else None

    @field_validator("AUTH_DATABASE_URL")
    @classmethod
    def validate_auth_database_url(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) and v.strip() else None

    @field_validator("AUTH_COOKIE_SAMESITE")
    @classmethod
    def validate_auth_cookie_samesite(cls, v: str) -> str:
        normalized = str(v).strip().lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("AUTH_COOKIE_SAMESITE deve ser lax, strict ou none.")
        return normalized

    @field_validator("AUTH_COOKIE_SECURE")
    @classmethod
    def validate_auth_cookie_secure(cls, v: bool, info) -> bool:
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production" and v is not True:
            raise ValueError("AUTH_COOKIE_SECURE deve ser true em produção.")
        return v

settings = Settings()

APP_NAME = settings.APP_NAME
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
ENCRYPTION_KEY = settings.ENCRYPTION_KEY
ALLOWED_ORIGINS = settings.get_cors_origins
DATABASE_URL = settings.DATABASE_URL
DATABASE_ECHO = settings.DATABASE_ECHO
