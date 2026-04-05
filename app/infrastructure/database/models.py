from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, Text, DateTime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)  # Recebe Hash Argon2
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class LeakRecord(Base):
    """ Tabela de Retenção de Vazamentos com Sigilo Absoluto """
    __tablename__ = "leak_records"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    encrypted_email: Mapped[str] = mapped_column(Text, index=True)  # E-mail mascarado AES-GCM
    encrypted_report: Mapped[str] = mapped_column(Text)             # Resultados mascarados


class RefreshTokenRecordModel(Base):
    __tablename__ = "refresh_tokens"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    sub: Mapped[str] = mapped_column(String, index=True)
    token_type: Mapped[str] = mapped_column(String(32), index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    parent_jti: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    compromised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
