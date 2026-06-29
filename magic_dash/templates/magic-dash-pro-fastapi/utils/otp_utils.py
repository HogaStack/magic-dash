import base64
import hashlib
import hmac
import time

from cryptography.fernet import Fernet

from configs import BaseConfig, OtpConfig


def validate_otp_config():
    """校验OTP动态口令相关配置"""

    if OtpConfig.otp_digits != 6:
        raise ValueError("OTP动态口令位数必须固定为6")

    if (
        not isinstance(OtpConfig.otp_interval_seconds, int)
        or OtpConfig.otp_interval_seconds <= 0
    ):
        raise ValueError("OTP动态口令刷新周期必须为正整数")

    if not isinstance(OtpConfig.otp_valid_window, int) or OtpConfig.otp_valid_window < 0:
        raise ValueError("OTP动态口令有效窗口偏移量不能为负数")

    if (
        not isinstance(OtpConfig.max_failed_attempts, int)
        or OtpConfig.max_failed_attempts <= 0
    ):
        raise ValueError("OTP动态口令最大失败次数必须为正整数")

    if not isinstance(OtpConfig.lockout_seconds, int) or OtpConfig.lockout_seconds <= 0:
        raise ValueError("OTP动态口令锁定时长必须为正整数")

    if not isinstance(OtpConfig.secret_length, int) or OtpConfig.secret_length < 32:
        raise ValueError("OTP密钥长度不能小于32")


def _load_pyotp():
    """按需加载pyotp依赖"""

    try:
        import pyotp

        return pyotp
    except ImportError as exc:
        raise RuntimeError("未安装pyotp依赖，请先执行pip install pyotp") from exc


def _get_secret_crypto():
    """构造用于OTP密钥加解密的Fernet实例"""

    key_material = OtpConfig.secret_crypto_key or BaseConfig.app_secret_key
    key = base64.urlsafe_b64encode(
        hashlib.sha256(str(key_material).encode("utf-8")).digest()
    )
    return Fernet(key)


def encrypt_otp_secret(secret: str) -> str:
    """加密OTP共享密钥"""

    if not secret:
        raise ValueError("OTP密钥不能为空")

    return _get_secret_crypto().encrypt(secret.encode("utf-8")).decode("utf-8")


def decrypt_otp_secret(secret_ciphertext: str) -> str:
    """解密OTP共享密钥"""

    if not secret_ciphertext:
        raise ValueError("OTP密钥密文不能为空")

    return (
        _get_secret_crypto().decrypt(secret_ciphertext.encode("utf-8")).decode("utf-8")
    )


def generate_otp_secret() -> str:
    """生成Base32格式OTP共享密钥"""

    validate_otp_config()
    pyotp = _load_pyotp()
    return pyotp.random_base32(length=OtpConfig.secret_length)


def get_totp(secret: str):
    """基于配置构造TOTP实例"""

    validate_otp_config()
    pyotp = _load_pyotp()
    return pyotp.TOTP(
        secret,
        digits=OtpConfig.otp_digits,
        interval=OtpConfig.otp_interval_seconds,
    )


def get_current_timecode() -> int:
    """获取当前TOTP时间窗口编号"""

    validate_otp_config()
    return int(time.time()) // OtpConfig.otp_interval_seconds


def build_otp_provisioning_uri(user_name: str, secret: str) -> str:
    """构建认证器App扫码绑定所需的otpauth地址"""

    return get_totp(secret).provisioning_uri(
        name=user_name,
        issuer_name=OtpConfig.issuer_name,
    )


def verify_otp_code(secret: str, otp_code: str):
    """校验6位数字TOTP动态口令，返回(是否有效, 命中的时间窗口)"""

    otp_code = str(otp_code or "").strip()
    if len(otp_code) != OtpConfig.otp_digits or not otp_code.isdigit():
        return False, None

    totp = get_totp(secret)
    current_timecode = get_current_timecode()

    for offset in range(-OtpConfig.otp_valid_window, OtpConfig.otp_valid_window + 1):
        timecode = current_timecode + offset
        if timecode < 0:
            continue
        candidate = totp.at(timecode * OtpConfig.otp_interval_seconds)
        if hmac.compare_digest(candidate, otp_code):
            return True, timecode

    return False, None
