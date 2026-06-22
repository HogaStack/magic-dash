import smtplib
import ssl
from datetime import datetime, timedelta
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from html import escape

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


def _format_expiration_time(expire_seconds: int) -> str:
    """生成带时区的验证码失效时间"""

    expires_at = datetime.now().astimezone() + timedelta(seconds=expire_seconds)
    utc_offset = expires_at.strftime("%z")
    if utc_offset:
        utc_offset = f"{utc_offset[:3]}:{utc_offset[3:]}"
    else:
        utc_offset = "+00:00"

    return f'{expires_at.strftime("%Y-%m-%d %H:%M:%S")} (UTC{utc_offset})'


def _build_verification_email(verification_code: str, expire_seconds: int):
    """构建兼容纯文本与HTML客户端的验证码邮件"""

    app_title = BaseConfig.app_title.strip()
    safe_app_title = escape(app_title)
    safe_verification_code = escape(verification_code)
    expires_at = _format_expiration_time(expire_seconds)

    plain_content = f"""{app_title} 登录验证码

你好，

我们收到了登录 {app_title} 的请求。
请在登录页面输入以下验证码：

{verification_code}

有效期至：{expires_at}

安全提示：请勿将验证码透露给任何人，包括平台工作人员。
如果这不是你的操作，可以忽略此邮件。

此邮件由 {app_title} 系统自动发送，请勿直接回复。"""

    html_content = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>{safe_app_title} 登录验证码</title>
</head>
<body style="margin:0;padding:0;background-color:#f3f6fb;color:#172033;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">
    验证码 {safe_verification_code}，有效期至 {expires_at}。
  </div>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background-color:#f3f6fb;">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="width:100%;max-width:600px;background-color:#ffffff;border:1px solid #e5eaf2;border-radius:14px;overflow:hidden;">
          <tr>
            <td style="height:5px;background-color:#006aff;font-size:0;line-height:0;">&nbsp;</td>
          </tr>
          <tr>
            <td style="padding:30px 40px 24px;border-bottom:1px solid #edf0f5;">
              <div style="font-family:'Segoe UI','Microsoft YaHei',sans-serif;font-size:22px;line-height:30px;font-weight:700;color:#172033;">{safe_app_title}</div>
              <div style="margin-top:3px;font-family:'Segoe UI','Microsoft YaHei',sans-serif;font-size:13px;line-height:20px;color:#768196;letter-spacing:1px;">安全验证</div>
            </td>
          </tr>
          <tr>
            <td style="padding:34px 40px 38px;">
              <h1 style="margin:0 0 18px;font-family:'Segoe UI','Microsoft YaHei',sans-serif;font-size:28px;line-height:38px;font-weight:700;color:#172033;">登录验证码</h1>
              <p style="margin:0 0 8px;font-family:'Segoe UI','Microsoft YaHei',sans-serif;font-size:15px;line-height:26px;color:#4d596c;">你好，</p>
              <p style="margin:0 0 24px;font-family:'Segoe UI','Microsoft YaHei',sans-serif;font-size:15px;line-height:26px;color:#4d596c;">我们收到了登录 {safe_app_title} 的请求。请在登录页面输入以下验证码：</p>

              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background-color:#f4f8ff;border:1px solid #cfe0ff;border-radius:10px;">
                <tr>
                  <td align="center" style="padding:26px 20px 10px;">
                    <div style="font-family:Consolas,'Courier New',monospace;font-size:38px;line-height:48px;font-weight:700;letter-spacing:9px;color:#005bd7;white-space:nowrap;">{safe_verification_code}</div>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding:0 20px 24px;font-family:'Segoe UI','Microsoft YaHei',sans-serif;font-size:13px;line-height:22px;color:#667085;">
                    有效期至：<strong style="font-weight:600;color:#344054;">{expires_at}</strong>
                  </td>
                </tr>
              </table>

              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;margin-top:24px;background-color:#f7f9fc;border-left:3px solid #006aff;">
                <tr>
                  <td style="padding:14px 16px;font-family:'Segoe UI','Microsoft YaHei',sans-serif;font-size:13px;line-height:22px;color:#596579;">
                    <strong style="display:block;margin-bottom:2px;color:#344054;">安全提示</strong>
                    请勿将验证码透露给任何人，包括平台工作人员。
                  </td>
                </tr>
              </table>

              <p style="margin:22px 0 0;font-family:'Segoe UI','Microsoft YaHei',sans-serif;font-size:14px;line-height:24px;color:#768196;">如果这不是你的操作，可以忽略此邮件。</p>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 40px;background-color:#fafbfc;border-top:1px solid #edf0f5;font-family:'Segoe UI','Microsoft YaHei',sans-serif;font-size:12px;line-height:20px;color:#8a94a6;">
              此邮件由 {safe_app_title} 系统自动发送，请勿直接回复。
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    message = MIMEMultipart("alternative")
    message.attach(MIMEText(plain_content, "plain", "utf-8"))
    message.attach(MIMEText(html_content, "html", "utf-8"))
    return message


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

    message = _build_verification_email(verification_code, expire_seconds)
    message["From"] = formataddr(
        (str(Header(EmailConfig.sender_name.strip(), "utf-8")), sender_email)
    )
    message["To"] = recipient_email
    message["Subject"] = Header(
        f"[{BaseConfig.app_title}] {verification_code} 是你的登录验证码",
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
