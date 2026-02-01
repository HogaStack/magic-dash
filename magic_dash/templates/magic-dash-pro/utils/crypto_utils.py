"""RSA加密解密工具模块

提供密码加密解密相关的功能，包括：
- 加载RSA公钥/私钥
- 解密前端传输的加密密码
"""

import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from configs import BaseConfig


def load_rsa_public_key():
    """加载RSA公钥文件内容

    从项目根目录读取public_key.pem文件

    Returns:
        str: 公钥PEM格式字符串
        None: 加载失败时返回None
    """

    with open(BaseConfig.rsa_public_key_path, "r", encoding="utf-8") as f:
        return f.read()


def decrypt_password(encrypted_base64: str) -> str:
    """使用RSA私钥解密前端传输的加密密码

    使用RSA-OAEP算法(SHA-256)解密Base64编码的加密密码

    Args:
        encrypted_base64: Base64编码的加密密码

    Returns:
        str: 解密后的明文密码
        None: 解密失败时返回None

    Example:
        >>> password = decrypt_password("AbCdEf123...")
        >>> print(password)
        "mypassword123"
    """

    if not encrypted_base64:
        return None

    try:
        # 读取私钥
        with open(BaseConfig.rsa_private_key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )

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
