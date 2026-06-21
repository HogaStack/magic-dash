from typing import Optional

from .base_config import BaseConfig


class EmailConfig:
    """邮箱验证码及SMTP服务配置参数"""

    # SMTP服务地址，例如163邮箱为smtp.163.com，QQ邮箱为smtp.qq.com
    smtp_server: str = ""

    # SMTP服务端口，例如普通连接通常使用25，SSL通常使用465，STARTTLS通常使用587
    smtp_port: Optional[int] = None

    # 用于发送验证码的邮箱地址
    sender_email: str = ""

    # 发件邮箱对应的SMTP授权码，通常不是邮箱登录密码
    sender_password: str = ""

    # 验证码邮件中展示的发件人名称
    sender_name: str = BaseConfig.app_title

    # 是否使用SSL方式连接SMTP服务，通常用于465端口
    smtp_use_ssl: bool = False

    # 是否在建立普通连接后启用STARTTLS加密，通常用于587端口
    smtp_use_starttls: bool = False

    # SMTP服务连接超时时间，单位：秒
    smtp_timeout: int = 10

    # 邮箱验证码有效期及重复发送等待时间，单位：秒
    verification_code_expire_seconds: int = 60

    # 单个邮箱验证码允许的最大错误校验次数
    verification_code_max_attempts: int = 5
