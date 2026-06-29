from .base_config import BaseConfig


class OtpConfig:
    """OTP动态口令登录配置参数"""

    # 认证器App中展示的发行方名称
    issuer_name: str = BaseConfig.app_title

    # OTP动态口令固定为6位数字
    otp_digits: int = 6

    # TOTP动态口令刷新周期，单位：秒
    otp_interval_seconds: int = 30

    # 允许前后偏移的时间窗口数量，用于兼容轻微时钟偏差
    otp_valid_window: int = 1

    # 连续校验失败达到该次数后，临时锁定OTP登录
    max_failed_attempts: int = 5

    # OTP登录临时锁定时长，单位：秒
    lockout_seconds: int = 300

    # 生成OTP密钥时使用的Base32字符串长度
    secret_length: int = 32

    # OTP密钥落库加密材料；生产环境建议设置为独立的高强度随机字符串
    secret_crypto_key: str = ""
