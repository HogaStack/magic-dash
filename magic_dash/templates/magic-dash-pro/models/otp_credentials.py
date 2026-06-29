from datetime import datetime, timedelta

from peewee import BooleanField, CharField, DateTimeField, IntegerField

from . import db, BaseModel


class OtpCredentials(BaseModel):
    """用户OTP动态口令凭据表模型类"""

    # 用户id，主键，对应Users.user_id
    user_id = CharField(primary_key=True)

    # 加密保存的TOTP共享密钥
    secret_ciphertext = CharField()

    # 是否已启用
    is_enabled = BooleanField(default=True)

    # 创建时间
    created_at = DateTimeField(default=datetime.now)

    # 绑定确认时间
    confirmed_at = DateTimeField(null=True)

    # 更新时间
    updated_at = DateTimeField(default=datetime.now)

    # 最近一次成功使用的TOTP时间窗口，防止同一口令重复使用
    last_used_timecode = IntegerField(null=True)

    # 连续失败次数
    failed_attempts = IntegerField(default=0)

    # 临时锁定截止时间
    locked_until = DateTimeField(null=True)

    @classmethod
    def ensure_table(cls):
        """确保OTP凭据表存在，用于兼容已初始化过的旧数据库"""

        with db.connection_context():
            if not cls.table_exists():
                db.create_tables([cls])

    @classmethod
    def get_credential(cls, user_id: str):
        """根据用户id查询OTP凭据信息"""

        user_id = (user_id or "").strip()
        if not user_id:
            return None

        cls.ensure_table()
        with db.connection_context():
            return cls.get_or_none(cls.user_id == user_id)

    @classmethod
    def has_enabled_otp(cls, user_id: str) -> bool:
        """判断用户是否已启用OTP动态口令"""

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
        with db.connection_context():
            with db.atomic():
                credential = cls.get_or_none(cls.user_id == user_id)
                if credential:
                    (
                        cls.update(
                            secret_ciphertext=secret_ciphertext,
                            is_enabled=True,
                            confirmed_at=now,
                            updated_at=now,
                            last_used_timecode=None,
                            failed_attempts=0,
                            locked_until=None,
                        )
                        .where(cls.user_id == user_id)
                        .execute()
                    )
                else:
                    cls.create(
                        user_id=user_id,
                        secret_ciphertext=secret_ciphertext,
                        is_enabled=True,
                        created_at=now,
                        confirmed_at=now,
                        updated_at=now,
                    )

            return cls.get_or_none(cls.user_id == user_id)

    @classmethod
    def disable_credential(cls, user_id: str):
        """解绑并删除指定用户OTP凭据"""

        user_id = (user_id or "").strip()
        if not user_id:
            return 0

        cls.ensure_table()
        with db.connection_context():
            return cls.delete().where(cls.user_id == user_id).execute()

    @staticmethod
    def is_locked(credential) -> bool:
        """判断OTP凭据是否处于临时锁定状态"""

        return bool(
            credential.locked_until and credential.locked_until > datetime.now()
        )

    @classmethod
    def mark_used(cls, user_id: str, timecode: int):
        """记录最近一次成功使用的TOTP时间窗口"""

        cls.ensure_table()
        with db.connection_context():
            return (
                cls.update(
                    last_used_timecode=timecode,
                    failed_attempts=0,
                    locked_until=None,
                    updated_at=datetime.now(),
                )
                .where(cls.user_id == user_id)
                .execute()
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
        with db.connection_context():
            credential = cls.get_or_none(cls.user_id == user_id)
            if not credential:
                return None

            failed_attempts = (credential.failed_attempts or 0) + 1
            locked_until = (
                datetime.now() + timedelta(seconds=lockout_seconds)
                if failed_attempts >= max_failed_attempts
                else credential.locked_until
            )

            (
                cls.update(
                    failed_attempts=failed_attempts,
                    locked_until=locked_until,
                    updated_at=datetime.now(),
                )
                .where(cls.user_id == user_id)
                .execute()
            )

            return cls.get_or_none(cls.user_id == user_id)

    @classmethod
    def reset_failed_attempts(cls, user_id: str):
        """清空OTP失败计数和锁定状态"""

        cls.ensure_table()
        with db.connection_context():
            return (
                cls.update(
                    failed_attempts=0,
                    locked_until=None,
                    updated_at=datetime.now(),
                )
                .where(cls.user_id == user_id)
                .execute()
            )
