from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, delete, update
from sqlmodel import Field

from . import BaseModel, create_tables, session_scope
from ..schema_contract import TABLE_NAMES


class OtpCredentials(BaseModel, table=True):
    """SQLModel版用户OTP动态口令凭据表模型"""

    __tablename__ = TABLE_NAMES["OtpCredentials"]

    user_id: str = Field(sa_column=Column(String(255), primary_key=True))
    secret_ciphertext: str = Field(sa_column=Column(String(255), nullable=False))
    is_enabled: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, nullable=False),
    )
    confirmed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, nullable=False),
    )
    last_used_timecode: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
    )
    failed_attempts: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False),
    )
    locked_until: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True),
    )

    @classmethod
    def ensure_table(cls):
        """确保OTP凭据表存在，用于兼容已初始化过的旧数据库"""

        if not cls.table_exists():
            create_tables([cls])

    @classmethod
    def get_credential(cls, user_id: str):
        user_id = (user_id or "").strip()
        if not user_id:
            return None
        cls.ensure_table()
        with session_scope() as session:
            return session.get(cls, user_id)

    @classmethod
    def has_enabled_otp(cls, user_id: str) -> bool:
        credential = cls.get_credential(user_id)
        return bool(credential and credential.is_enabled)

    @classmethod
    def enable_credential(cls, user_id: str, secret_ciphertext: str):
        """创建或覆盖启用用户OTP凭据"""

        user_id = (user_id or "").strip()
        if not user_id or not secret_ciphertext:
            raise ValueError("OTP凭据信息不完整")

        cls.ensure_table()
        now = datetime.now()
        with session_scope() as session:
            credential = session.get(cls, user_id)
            if credential:
                session.execute(
                    update(cls)
                    .where(cls.user_id == user_id)
                    .values(
                        secret_ciphertext=secret_ciphertext,
                        is_enabled=True,
                        confirmed_at=now,
                        updated_at=now,
                        last_used_timecode=None,
                        failed_attempts=0,
                        locked_until=None,
                    )
                )
            else:
                session.add(
                    cls(
                        user_id=user_id,
                        secret_ciphertext=secret_ciphertext,
                        is_enabled=True,
                        created_at=now,
                        confirmed_at=now,
                        updated_at=now,
                    )
                )
            session.flush()
            return session.get(cls, user_id)

    @classmethod
    def disable_credential(cls, user_id: str):
        user_id = (user_id or "").strip()
        if not user_id:
            return 0
        cls.ensure_table()
        with session_scope() as session:
            return (
                session.execute(delete(cls).where(cls.user_id == user_id)).rowcount or 0
            )

    @staticmethod
    def is_locked(credential) -> bool:
        return bool(
            credential.locked_until and credential.locked_until > datetime.now()
        )

    @classmethod
    def mark_used(cls, user_id: str, timecode: int):
        cls.ensure_table()
        with session_scope() as session:
            return (
                session.execute(
                    update(cls)
                    .where(cls.user_id == user_id)
                    .values(
                        last_used_timecode=timecode,
                        failed_attempts=0,
                        locked_until=None,
                        updated_at=datetime.now(),
                    )
                ).rowcount
                or 0
            )

    @classmethod
    def record_failed_attempt(
        cls,
        user_id: str,
        max_failed_attempts: int,
        lockout_seconds: int,
    ):
        """记录OTP校验失败，并在达到阈值后临时锁定"""

        cls.ensure_table()
        with session_scope() as session:
            credential = session.get(cls, user_id)
            if not credential:
                return None

            failed_attempts = (credential.failed_attempts or 0) + 1
            locked_until = (
                datetime.now() + timedelta(seconds=lockout_seconds)
                if failed_attempts >= max_failed_attempts
                else credential.locked_until
            )

            session.execute(
                update(cls)
                .where(cls.user_id == user_id)
                .values(
                    failed_attempts=failed_attempts,
                    locked_until=locked_until,
                    updated_at=datetime.now(),
                )
            )
            session.flush()
            return session.get(cls, user_id)

    @classmethod
    def reset_failed_attempts(cls, user_id: str):
        cls.ensure_table()
        with session_scope() as session:
            return (
                session.execute(
                    update(cls)
                    .where(cls.user_id == user_id)
                    .values(
                        failed_attempts=0,
                        locked_until=None,
                        updated_at=datetime.now(),
                    )
                ).rowcount
                or 0
            )
