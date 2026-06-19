"""通用数据校验工具模块"""

import re


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def validate_optional_email(value):
    """校验可选邮箱地址"""

    value = (value or "").strip()

    return not value or bool(EMAIL_PATTERN.match(value))
