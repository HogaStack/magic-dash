import math
import secrets
from datetime import datetime, timedelta

from peewee import CharField, DateTimeField, IntegerField, IntegrityError

from . import db, BaseModel


class EmailVerifications(BaseModel):
    """邮箱验证码信息表模型类"""

    # 邮箱地址，主键且唯一
    email = CharField(primary_key=True)

    # 6位数字验证码
    verification_code = CharField(max_length=6)

    # 验证码生成时间
    generated_at = DateTimeField(default=datetime.now)

    # 当前验证码累计错误校验次数
    failed_attempts = IntegerField(default=0)

    @staticmethod
    def generate_code() -> str:
        """生成6位数字验证码"""

        return f"{secrets.randbelow(1000000):06d}"

    @staticmethod
    def _validate_expire_seconds(expire_seconds: int):
        """校验验证码有效期参数"""

        if not isinstance(expire_seconds, int) or expire_seconds <= 0:
            raise ValueError("邮箱验证码有效期必须为正整数")

    @staticmethod
    def _get_record_remaining_seconds(verification, expire_seconds: int) -> int:
        """计算验证码记录的剩余有效秒数"""

        expires_at = verification.generated_at + timedelta(seconds=expire_seconds)
        return max(0, math.ceil((expires_at - datetime.now()).total_seconds()))

    @classmethod
    def get_verification(cls, email: str):
        """根据邮箱获取验证码记录"""

        email = (email or "").strip()
        if not email:
            return None

        with db.connection_context():
            return cls.get_or_none(cls.email == email)

    @classmethod
    def issue_verification(cls, email: str, expire_seconds: int):
        """为无有效验证码的邮箱签发新验证码"""

        email = (email or "").strip()
        if not email:
            raise ValueError("邮箱不能为空")
        cls._validate_expire_seconds(expire_seconds)

        verification_code = cls.generate_code()

        with db.connection_context():
            # 条件更新与主键插入共同保证并发请求中仅一方可以成功签发。
            for _ in range(3):
                generated_at = datetime.now()
                expired_before = generated_at - timedelta(seconds=expire_seconds)

                with db.atomic():
                    updated_count = (
                        cls.update(
                            verification_code=verification_code,
                            generated_at=generated_at,
                            failed_attempts=0,
                        )
                        .where(
                            (cls.email == email) & (cls.generated_at <= expired_before)
                        )
                        .execute()
                    )

                if updated_count:
                    return cls.get_by_id(email), 0

                try:
                    with db.atomic():
                        cls.create(
                            email=email,
                            verification_code=verification_code,
                            generated_at=generated_at,
                            failed_attempts=0,
                        )
                    return cls.get_by_id(email), 0
                except IntegrityError:
                    verification = cls.get_or_none(cls.email == email)
                    if verification:
                        remaining_seconds = cls._get_record_remaining_seconds(
                            verification,
                            expire_seconds,
                        )
                        if remaining_seconds > 0:
                            return None, remaining_seconds

            raise RuntimeError("邮箱验证码签发失败，请稍后重试")

    @classmethod
    def get_remaining_seconds(cls, email: str, expire_seconds: int) -> int:
        """获取指定邮箱当前验证码的剩余有效秒数"""

        cls._validate_expire_seconds(expire_seconds)

        for _ in range(3):
            verification = cls.get_verification(email)
            if not verification:
                return 0

            remaining_seconds = cls._get_record_remaining_seconds(
                verification,
                expire_seconds,
            )
            if remaining_seconds > 0:
                return remaining_seconds

            deleted_count = cls.delete_verification(
                email,
                verification.verification_code,
                verification.generated_at,
            )
            if deleted_count:
                return 0

        return 0

    @classmethod
    def verify_code(
        cls,
        email: str,
        verification_code: str,
        expire_seconds: int,
        max_attempts: int,
    ):
        """校验验证码，并在成功或过期时消费对应记录"""

        email = (email or "").strip()
        verification_code = (verification_code or "").strip()
        cls._validate_expire_seconds(expire_seconds)
        if not isinstance(max_attempts, int) or max_attempts <= 0:
            raise ValueError("邮箱验证码最大错误校验次数必须为正整数")

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

                if verification.failed_attempts >= max_attempts:
                    return "too_many_attempts"

                if not secrets.compare_digest(
                    verification.verification_code,
                    verification_code,
                ):
                    updated_count = (
                        cls.update(failed_attempts=cls.failed_attempts + 1)
                        .where(
                            (cls.email == email)
                            & (cls.verification_code == verification.verification_code)
                            & (cls.generated_at == verification.generated_at)
                        )
                        .execute()
                    )
                    if not updated_count:
                        continue

                    latest_verification = cls.get_or_none(cls.email == email)
                    if (
                        latest_verification
                        and latest_verification.failed_attempts >= max_attempts
                    ):
                        return "too_many_attempts"
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
