import os
import uuid
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core import config as app_config

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    issued_at = datetime.now(timezone.utc)
    if expires_delta:
        expire = issued_at + expires_delta
    else:
        expire = issued_at + timedelta(minutes=app_config.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": issued_at})
    encoded_jwt = jwt.encode(to_encode, app_config.SECRET_KEY, algorithm=app_config.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    issued_at = datetime.now(timezone.utc)
    to_encode = {"sub": data.get("sub")}
    if expires_delta:
        expire = issued_at + expires_delta
    else:
        expire = issued_at + timedelta(days=app_config.REFRESH_TOKEN_EXPIRE_DAYS)

    # `jti` prepara revogação/rotação futuras sem quebrar o formato atual do token.
    to_encode.update({"exp": expire, "iat": issued_at, "type": "refresh", "jti": uuid.uuid4().hex})
    if data.get("parent_jti"):
        to_encode["parent_jti"] = data["parent_jti"]
    encoded_jwt = jwt.encode(to_encode, app_config.SECRET_KEY, algorithm=app_config.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, app_config.SECRET_KEY, algorithms=[app_config.ALGORITHM])
    except JWTError as exc:
        raise ValueError("Token inválido.") from exc


def validate_access_token(token: str) -> dict:
    claims = decode_token(token)
    if not claims.get("sub"):
        raise ValueError("Access token inválido.")
    if claims.get("type") == "refresh":
        raise ValueError("Access token inválido.")
    return claims


def validate_refresh_token(token: str, revocation_checker=None) -> dict:
    claims = decode_token(token)
    if claims.get("type") != "refresh":
        raise ValueError("Refresh token inválido.")
    if not claims.get("sub"):
        raise ValueError("Refresh token inválido.")
    if not claims.get("jti"):
        raise ValueError("Refresh token inválido.")
    if revocation_checker and revocation_checker(claims["jti"]):
        raise ValueError("Refresh token revogado.")
    return claims

def encrypt_sensitive_data(plain_text: str) -> str:
    """Criptografa payloads sensíveis com AES-256-GCM."""
    key_bytes = bytes.fromhex(app_config.ENCRYPTION_KEY)
    aesgcm = AESGCM(key_bytes)

    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plain_text.encode('utf-8'), None)

    return f"{nonce.hex()}:{ct.hex()}"

def decrypt_sensitive_data(encrypted_payload: str) -> str:
    """Descriptografa payloads sensíveis armazenados com AES-256-GCM.

    Nunca registre em log o payload descriptografado.
    """
    try:
        key_bytes = bytes.fromhex(app_config.ENCRYPTION_KEY)
        nonce_hex, ct_hex = encrypted_payload.split(':')

        nonce = bytes.fromhex(nonce_hex)
        ct = bytes.fromhex(ct_hex)

        aesgcm = AESGCM(key_bytes)
        plain_text_bytes = aesgcm.decrypt(nonce, ct, None)
        return plain_text_bytes.decode('utf-8')
    except Exception:
        raise ValueError("Falha ao descriptografar dado sensível.")
