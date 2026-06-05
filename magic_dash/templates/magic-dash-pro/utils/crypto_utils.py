"""登录密码字段处理工具模块

提供密码字段还原相关的功能，包括：
- 按需加载RSA公钥/私钥
- 解密前端传输的RSA加密密码
- 还原未开启RSA时的前端密码字段转换结果
"""

import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from configs import BaseConfig


def load_rsa_public_key():
    """按需加载RSA公钥"""

    if not BaseConfig.enable_login_rsa_crypto:
        return None

    try:
        with open(BaseConfig.rsa_public_key_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"RSA公钥加载失败: {e}")
        return None


def load_rsa_private_key():
    """按需加载RSA私钥"""

    try:
        with open(BaseConfig.rsa_private_key_path, "rb") as f:
            return serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )
    except Exception as e:
        print(f"RSA私钥加载失败: {e}")
        return None


rsa_public_key = load_rsa_public_key()


def decrypt_password(encrypted_base64: str) -> str:
    """使用RSA私钥解密前端传输的加密密码

    使用RSA-OAEP算法(SHA-256)解密Base64编码的加密密码

    Args:
        encrypted_base64: Base64编码的加密密码

    Returns:
        str: 解密后的明文密码
        None: 解密失败时返回None

    Example:
        >>> decrypt_password("AbCdEf123...")
        "mypassword123"
    """

    if not encrypted_base64:
        return None

    try:
        private_key = load_rsa_private_key()
        if private_key is None:
            return None

        # Base64解码加密数据
        encrypted_data = base64.b64decode(encrypted_base64)

        # RSA-OAEP解密
        decrypted_data = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

        return decrypted_data.decode("utf-8")
    except Exception as e:
        print(f"密码解密失败: {e}")
        return None


def restore_obfuscated_password(obfuscated_password: str) -> str:
    """还原未开启RSA时前端传输的密码字段值"""

    if not obfuscated_password:
        return None

    return obfuscated_password[::2][::-1]


def restore_login_password(password_payload: str, enable_rsa_crypto: bool) -> str:
    """根据当前项目配置还原前端传输的登录密码字段值"""

    if not password_payload:
        return None

    if enable_rsa_crypto:
        return decrypt_password(password_payload)

    return restore_obfuscated_password(password_payload)
