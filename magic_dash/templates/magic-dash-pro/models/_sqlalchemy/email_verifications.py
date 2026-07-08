import math
import secrets
from datetime import datetime, timedelta

from sqlalchemy import DateTime, String, delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel, session_scope
from ..schema_contract import TABLE_NAMES


class EmailVerifications(BaseModel):
    """SQLAlchemy版邮箱验证码信息表模型"""

    __tablename__ = TABLE_NAMES["EmailVerifications"]

    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    verification_code: Mapped[str] = mapped_column(String(6))
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    @staticmethod
    def generate_code() -> str:
        return f"{secrets.randbelow(1000000):06d}"

    @staticmethod
    def _validate_seconds(seconds: int, parameter_name: str):
        if not isinstance(seconds, int) or seconds <= 0:
            raise ValueError(f"{parameter_name}必须为正整数")

    @staticmethod
    def _get_record_remaining_seconds(verification, interval_seconds: int) -> int:
        interval_ends_at = verification.generated_at + timedelta(
            seconds=interval_seconds
        )
        return max(0, math.ceil((interval_ends_at - datetime.now()).total_seconds()))

    @classmethod
    def get_verification(cls, email: str):
        email = (email or "").strip()
        if not email:
            return None
        with session_scope() as session:
            return session.get(cls, email)

    @classmethod
    def issue_verification(cls, email: str, resend_interval_seconds: int):
        """签发验证码，通过条件更新避免并发请求互相覆盖"""

        email = (email or "").strip()
        if not email:
            raise ValueError("邮箱不能为空")
        cls._validate_seconds(
            resend_interval_seconds,
            "邮箱验证码重复发送等待时间",
        )

        verification_code = cls.generate_code()

        for _ in range(3):
            generated_at = datetime.now()
            resend_before = generated_at - timedelta(seconds=resend_interval_seconds)

            with session_scope() as session:
                previous_verification = session.get(cls, email)
                if previous_verification:
                    remaining_seconds = cls._get_record_remaining_seconds(
                        previous_verification,
                        resend_interval_seconds,
                    )
                    if remaining_seconds > 0:
                        return None, remaining_seconds, None

                    previous_snapshot = cls(
                        email=previous_verification.email,
                        verification_code=previous_verification.verification_code,
                        generated_at=previous_verification.generated_at,
                    )
                    updated_count = (
                        session.execute(
                            update(cls)
                            .where(
                                (cls.email == email)
                                & (
                                    cls.verification_code
                                    == previous_verification.verification_code
                                )
                                & (
                                    cls.generated_at
                                    == previous_verification.generated_at
                                )
                                & (cls.generated_at <= resend_before)
                            )
                            .values(
                                verification_code=verification_code,
                                generated_at=generated_at,
                            )
                        ).rowcount
                        or 0
                    )
                    if updated_count:
                        session.flush()
                        return session.get(cls, email), 0, previous_snapshot
                    continue

                try:
                    verification = cls(
                        email=email,
                        verification_code=verification_code,
                        generated_at=generated_at,
                    )
                    session.add(verification)
                    session.flush()
                    return verification, 0, None
                except IntegrityError:
                    session.rollback()
                    continue

        raise RuntimeError("邮箱验证码签发失败，请稍后重试")

    @classmethod
    def get_resend_remaining_seconds(
        cls,
        email: str,
        resend_interval_seconds: int,
    ) -> int:
        cls._validate_seconds(
            resend_interval_seconds,
            "邮箱验证码重复发送等待时间",
        )
        verification = cls.get_verification(email)
        if not verification:
            return 0
        return cls._get_record_remaining_seconds(
            verification,
            resend_interval_seconds,
        )

    @classmethod
    def verify_code(
        cls,
        email: str,
        verification_code: str,
        expire_seconds: int,
    ):
        """校验验证码，成功或过期时消费对应记录"""

        email = (email or "").strip()
        verification_code = (verification_code or "").strip()
        cls._validate_seconds(expire_seconds, "邮箱验证码有效期")

        for _ in range(3):
            verification = cls.get_verification(email)
            if not verification:
                return "not_found"

            remaining_seconds = cls._get_record_remaining_seconds(
                verification,
                expire_seconds,
            )
            if remaining_seconds <= 0:
                deleted_count = cls.delete_verification(
                    email,
                    verification.verification_code,
                    verification.generated_at,
                )
                if deleted_count:
                    return "expired"
                continue

            if not secrets.compare_digest(
                verification.verification_code,
                verification_code,
            ):
                return "invalid"

            deleted_count = cls.delete_verification(
                email,
                verification.verification_code,
                verification.generated_at,
            )
            if deleted_count:
                return "valid"

        return "invalid"

    @classmethod
    def rollback_issued_verification(cls, verification, previous_verification=None):
        """邮件发送失败时回滚本次签发，且不覆盖并发产生的新记录"""

        with session_scope() as session:
            current_record_filter = (
                (cls.email == verification.email)
                & (cls.verification_code == verification.verification_code)
                & (cls.generated_at == verification.generated_at)
            )
            if previous_verification:
                return (
                    session.execute(
                        update(cls)
                        .where(current_record_filter)
                        .values(
                            verification_code=previous_verification.verification_code,
                            generated_at=previous_verification.generated_at,
                        )
                    ).rowcount
                    or 0
                )
            return (
                session.execute(delete(cls).where(current_record_filter)).rowcount or 0
            )

    @classmethod
    def delete_verification(
        cls,
        email: str,
        verification_code: str = None,
        generated_at: datetime = None,
    ):
        with session_scope() as session:
            query = delete(cls).where(cls.email == (email or "").strip())
            if verification_code:
                query = query.where(cls.verification_code == verification_code)
            if generated_at:
                query = query.where(cls.generated_at == generated_at)
            return session.execute(query).rowcount or 0
