import smtplib
import ssl
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

from configs import BaseConfig, EmailConfig
from .validation_utils import validate_optional_email


def _validate_email_config():
    """校验发送邮件所需配置"""

    if (
        not isinstance(EmailConfig.smtp_server, str)
        or not EmailConfig.smtp_server.strip()
    ):
        raise ValueError("未配置SMTP服务地址")
    if (
        not isinstance(EmailConfig.sender_email, str)
        or not EmailConfig.sender_email.strip()
    ):
        raise ValueError("未配置发件邮箱地址")
    if not validate_optional_email(EmailConfig.sender_email):
        raise ValueError("发件邮箱地址格式不正确")
    if (
        not isinstance(EmailConfig.sender_name, str)
        or not EmailConfig.sender_name.strip()
    ):
        raise ValueError("未配置发件人显示名称")
    if (
        not isinstance(EmailConfig.sender_password, str)
        or not EmailConfig.sender_password
    ):
        raise ValueError("未配置发件邮箱SMTP授权码")
    if (
        not isinstance(EmailConfig.smtp_port, int)
        or not 1 <= EmailConfig.smtp_port <= 65535
    ):
        raise ValueError("SMTP服务端口不正确")
    if (
        not isinstance(EmailConfig.smtp_timeout, (int, float))
        or EmailConfig.smtp_timeout <= 0
    ):
        raise ValueError("SMTP服务连接超时时间必须大于0秒")
    if EmailConfig.smtp_use_ssl and EmailConfig.smtp_use_starttls:
        raise ValueError("SMTP SSL与STARTTLS不能同时开启")
    if (
        not isinstance(EmailConfig.verification_code_expire_seconds, int)
        or EmailConfig.verification_code_expire_seconds <= 0
    ):
        raise ValueError("邮箱验证码有效期必须为正整数")


def send_email_verification_code(recipient_email: str, verification_code: str):
    """向指定邮箱发送登录验证码"""

    _validate_email_config()
    if (
        not isinstance(recipient_email, str)
        or not recipient_email.strip()
        or not validate_optional_email(recipient_email)
    ):
        raise ValueError("收件邮箱地址格式不正确")
    if (
        not isinstance(verification_code, str)
        or len(verification_code) != 6
        or not verification_code.isdigit()
    ):
        raise ValueError("邮箱验证码必须是6位数字")

    smtp_server = EmailConfig.smtp_server.strip()
    sender_email = EmailConfig.sender_email.strip()
    recipient_email = recipient_email.strip()
    expire_seconds = EmailConfig.verification_code_expire_seconds

    message = MIMEText(
        "您的邮箱登录验证码是：{}。验证码将在{}秒后失效，请勿向他人泄露。".format(
            verification_code, expire_seconds
        ),
        "plain",
        "utf-8",
    )
    message["From"] = formataddr(
        (str(Header(EmailConfig.sender_name.strip(), "utf-8")), sender_email)
    )
    message["To"] = recipient_email
    message["Subject"] = Header(
        f"{BaseConfig.app_title} 邮箱登录验证码",
        "utf-8",
    )

    ssl_context = ssl.create_default_context()

    smtp_client = None

    try:
        if EmailConfig.smtp_use_ssl:
            smtp_client = smtplib.SMTP_SSL(
                smtp_server,
                EmailConfig.smtp_port,
                timeout=EmailConfig.smtp_timeout,
                context=ssl_context,
            )
        else:
            smtp_client = smtplib.SMTP(
                smtp_server,
                EmailConfig.smtp_port,
                timeout=EmailConfig.smtp_timeout,
            )

        smtp_client.ehlo()
        if EmailConfig.smtp_use_starttls:
            smtp_client.starttls(context=ssl_context)
            smtp_client.ehlo()
        smtp_client.login(
            sender_email,
            EmailConfig.sender_password,
        )
        smtp_client.sendmail(
            sender_email,
            recipient_email,
            message.as_string(),
        )
    finally:
        if smtp_client:
            try:
                smtp_client.quit()
            except Exception:
                try:
                    smtp_client.close()
                except Exception:
                    pass
