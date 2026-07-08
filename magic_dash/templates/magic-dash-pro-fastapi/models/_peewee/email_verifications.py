import math
import secrets
from datetime import datetime, timedelta

from peewee import CharField, DateTimeField, IntegrityError

from . import db, BaseModel
from ..schema_contract import TABLE_NAMES


class EmailVerifications(BaseModel):
    """邮箱验证码信息表模型类"""

    # 邮箱地址，主键且唯一
    email = CharField(primary_key=True)

    # 6位数字验证码
    verification_code = CharField(max_length=6)

    # 验证码生成时间
    generated_at = DateTimeField(default=datetime.now)

    class Meta:
        # 显式声明表名，确保不同ORM引擎映射到同一张物理表
        database = db
        table_name = TABLE_NAMES["EmailVerifications"]

    @staticmethod
    def generate_code() -> str:
        """生成6位数字验证码"""

        return f"{secrets.randbelow(1000000):06d}"

    @staticmethod
    def _validate_seconds(seconds: int, parameter_name: str):
        """校验以秒为单位的正整数参数"""

        if not isinstance(seconds, int) or seconds <= 0:
            raise ValueError(f"{parameter_name}必须为正整数")

    @staticmethod
    def _get_record_remaining_seconds(verification, interval_seconds: int) -> int:
        """计算验证码记录距离指定时间间隔结束的剩余秒数"""

        interval_ends_at = verification.generated_at + timedelta(
            seconds=interval_seconds
        )
        return max(0, math.ceil((interval_ends_at - datetime.now()).total_seconds()))

    @classmethod
    def get_verification(cls, email: str):
        """根据邮箱获取验证码记录"""

        email = (email or "").strip()
        if not email:
            return None

        with db.connection_context():
            return cls.get_or_none(cls.email == email)

    @classmethod
    def issue_verification(cls, email: str, resend_interval_seconds: int):
        """在重复发送等待时间结束后为邮箱签发新验证码"""

        email = (email or "").strip()
        if not email:
            raise ValueError("邮箱不能为空")
        cls._validate_seconds(
            resend_interval_seconds,
            "邮箱验证码重复发送等待时间",
        )

        verification_code = cls.generate_code()

        with db.connection_context():
            # 比对旧记录后再条件更新，保证并发请求中仅一方可以成功签发，
            # 同时保留旧记录快照，供邮件发送失败时安全恢复。
            for _ in range(3):
                generated_at = datetime.now()
                resend_before = generated_at - timedelta(
                    seconds=resend_interval_seconds
                )
                previous_verification = cls.get_or_none(cls.email == email)

                if previous_verification:
                    remaining_seconds = cls._get_record_remaining_seconds(
                        previous_verification,
                        resend_interval_seconds,
                    )
                    if remaining_seconds > 0:
                        return None, remaining_seconds, None

                    with db.atomic():
                        updated_count = (
                            cls.update(
                                verification_code=verification_code,
                                generated_at=generated_at,
                            )
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
                            .execute()
                        )

                    if updated_count:
                        return cls.get_by_id(email), 0, previous_verification
                    continue

                try:
                    with db.atomic():
                        cls.create(
                            email=email,
                            verification_code=verification_code,
                            generated_at=generated_at,
                        )
                    return cls.get_by_id(email), 0, None
                except IntegrityError:
                    continue

            raise RuntimeError("邮箱验证码签发失败，请稍后重试")

    @classmethod
    def get_resend_remaining_seconds(
        cls,
        email: str,
        resend_interval_seconds: int,
    ) -> int:
        """获取指定邮箱再次发送验证码前的剩余等待秒数"""

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
        """校验验证码，并在成功或过期时消费对应记录"""

        email = (email or "").strip()
        verification_code = (verification_code or "").strip()
        cls._validate_seconds(expire_seconds, "邮箱验证码有效期")
        with db.connection_context():
            for _ in range(3):
                verification = cls.get_or_none(cls.email == email)
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

        with db.connection_context():
            current_record_filter = (
                (cls.email == verification.email)
                & (cls.verification_code == verification.verification_code)
                & (cls.generated_at == verification.generated_at)
            )
            if previous_verification:
                return (
                    cls.update(
                        verification_code=previous_verification.verification_code,
                        generated_at=previous_verification.generated_at,
                    )
                    .where(current_record_filter)
                    .execute()
                )
            return cls.delete().where(current_record_filter).execute()

    @classmethod
    def delete_verification(
        cls,
        email: str,
        verification_code: str = None,
        generated_at: datetime = None,
    ):
        """删除指定邮箱的验证码，可限制仅删除匹配验证码的记录"""

        with db.connection_context():
            query = cls.delete().where(cls.email == (email or "").strip())
            if verification_code:
                query = query.where(cls.verification_code == verification_code)
            if generated_at:
                query = query.where(cls.generated_at == generated_at)

            return query.execute()
