import importlib
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from email import message_from_string
from pathlib import Path
from unittest.mock import patch

import pytest


TEMPLATE_ROOT = (
    Path(__file__).resolve().parents[1] / "magic_dash" / "templates" / "magic-dash-pro-fastapi"
)


def clear_template_modules():
    """清理以顶层包名导入的模板模块，隔离临时数据库。"""

    for module_name in list(sys.modules):
        if module_name == "models" or module_name.startswith("models."):
            sys.modules.pop(module_name)
        elif module_name == "configs" or module_name.startswith("configs."):
            sys.modules.pop(module_name)


@pytest.fixture
def email_utils(monkeypatch):
    clear_template_modules()
    sys.modules.pop("utils.email_utils", None)
    monkeypatch.syspath_prepend(str(TEMPLATE_ROOT))

    module = importlib.import_module("utils.email_utils")
    config_module = importlib.import_module("configs")

    yield module, config_module.EmailConfig

    sys.modules.pop("utils.email_utils", None)
    clear_template_modules()


@pytest.fixture
def email_verification_model(tmp_path, monkeypatch):
    pytest.importorskip("peewee")
    clear_template_modules()
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(TEMPLATE_ROOT))

    module = importlib.import_module("models.email_verifications")
    module.db.create_tables([module.EmailVerifications])

    yield module.EmailVerifications

    if not module.db.is_closed():
        module.db.close()
    clear_template_modules()


def test_verification_issue_refresh_and_single_use(
    email_verification_model,
    monkeypatch,
):
    model = email_verification_model
    verification_codes = iter(["111111", "222222", "333333"])
    monkeypatch.setattr(
        model,
        "generate_code",
        staticmethod(lambda: next(verification_codes)),
    )

    first_verification, remaining_seconds = model.issue_verification(
        "user@example.com",
        60,
    )
    assert first_verification.verification_code == "111111"
    assert remaining_seconds == 0

    blocked_verification, remaining_seconds = model.issue_verification(
        "user@example.com",
        60,
    )
    assert blocked_verification is None
    assert 1 <= remaining_seconds <= 60
    assert model.get_verification("user@example.com").verification_code == "111111"

    (
        model.update(generated_at=datetime.now() - timedelta(seconds=61))
        .where(model.email == "user@example.com")
        .execute()
    )
    refreshed_verification, remaining_seconds = model.issue_verification(
        "user@example.com",
        60,
    )
    assert refreshed_verification.verification_code == "333333"
    assert remaining_seconds == 0

    assert model.verify_code("user@example.com", "000000", 60, 5) == "invalid"
    assert model.get_verification("user@example.com") is not None
    assert model.verify_code("user@example.com", "333333", 60, 5) == "valid"
    assert model.verify_code("user@example.com", "333333", 60, 5) == "not_found"


def test_verification_rejects_attempts_after_limit(
    email_verification_model,
    monkeypatch,
):
    model = email_verification_model
    monkeypatch.setattr(
        model,
        "generate_code",
        staticmethod(lambda: "123456"),
    )
    model.issue_verification("user@example.com", 60)

    for _ in range(4):
        assert model.verify_code("user@example.com", "000000", 60, 5) == "invalid"

    assert model.verify_code("user@example.com", "000000", 60, 5) == "too_many_attempts"
    assert model.verify_code("user@example.com", "123456", 60, 5) == "too_many_attempts"


def test_expired_cleanup_does_not_delete_refreshed_verification(
    email_verification_model,
):
    model = email_verification_model
    old_generated_at = datetime.now() - timedelta(seconds=61)
    model.create(
        email="user@example.com",
        verification_code="111111",
        generated_at=old_generated_at,
    )

    new_generated_at = datetime.now()
    (
        model.update(
            verification_code="222222",
            generated_at=new_generated_at,
        )
        .where(model.email == "user@example.com")
        .execute()
    )

    deleted_count = model.delete_verification(
        "user@example.com",
        "111111",
        old_generated_at,
    )
    assert deleted_count == 0
    assert model.get_verification("user@example.com").verification_code == "222222"


def test_concurrent_issue_allows_only_one_active_verification(
    email_verification_model,
):
    model = email_verification_model
    start_barrier = threading.Barrier(2)

    def issue_verification():
        start_barrier.wait()
        return model.issue_verification("user@example.com", 60)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: issue_verification(), range(2)))

    issued_count = sum(verification is not None for verification, _ in results)
    blocked_count = sum(remaining > 0 for _, remaining in results)

    assert issued_count == 1
    assert blocked_count == 1
    assert model.select().where(model.email == "user@example.com").count() == 1


def test_magic_init_upgrades_legacy_verification_table(tmp_path, monkeypatch):
    pytest.importorskip("peewee")
    clear_template_modules()
    sys.modules.pop("magic_init", None)
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(TEMPLATE_ROOT))

    model_module = importlib.import_module("models.email_verifications")
    table_name = model_module.EmailVerifications._meta.table_name
    model_module.db.execute_sql(
        f"CREATE TABLE {table_name} ("
        "email VARCHAR(255) PRIMARY KEY, "
        "verification_code VARCHAR(6) NOT NULL, "
        "generated_at DATETIME NOT NULL)"
    )

    magic_init = importlib.import_module("magic_init")
    assert magic_init.ensure_email_verification_schema()
    assert "failed_attempts" in {
        column.name for column in model_module.db.get_columns(table_name)
    }
    assert not magic_init.ensure_email_verification_schema()

    if not model_module.db.is_closed():
        model_module.db.close()
    sys.modules.pop("magic_init", None)
    clear_template_modules()


def test_magic_init_always_creates_verification_table(tmp_path, monkeypatch):
    pytest.importorskip("peewee")
    clear_template_modules()
    sys.modules.pop("magic_init", None)
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(TEMPLATE_ROOT))

    magic_init = importlib.import_module("magic_init")
    monkeypatch.setattr(magic_init, "ask_admin_email", lambda: None)
    assert not magic_init.BaseConfig.enable_email_login

    magic_init.main()

    assert magic_init.EmailVerifications.table_exists()
    if not magic_init.db.is_closed():
        magic_init.db.close()
    sys.modules.pop("magic_init", None)
    clear_template_modules()


def test_send_email_uses_configured_smtp_authorization(email_utils):
    module, email_config = email_utils
    email_config.smtp_server = " smtp.163.com "
    email_config.smtp_port = 25
    email_config.sender_email = " sender@163.com "
    email_config.sender_password = "smtp-auth-code"
    email_config.smtp_use_ssl = False
    email_config.smtp_use_starttls = False

    with patch.object(module.smtplib, "SMTP") as smtp_class:
        smtp_client = smtp_class.return_value
        module.send_email_verification_code(" recipient@qq.com ", "012345")

    smtp_class.assert_called_once_with("smtp.163.com", 25, timeout=10)
    smtp_client.login.assert_called_once_with(
        "sender@163.com",
        "smtp-auth-code",
    )
    send_args = smtp_client.sendmail.call_args.args
    assert send_args[0] == "sender@163.com"
    assert send_args[1] == "recipient@qq.com"


def test_verification_email_contains_styled_html_and_plain_text(email_utils):
    module, email_config = email_utils
    email_config.smtp_server = "smtp.example.com"
    email_config.smtp_port = 25
    email_config.sender_email = "sender@example.com"
    email_config.sender_password = "smtp-auth-code"
    module.BaseConfig.app_title = "Internal Console"

    with patch.object(module.smtplib, "SMTP") as smtp_class:
        module.send_email_verification_code("user@example.com", "012345")

    raw_message = smtp_class.return_value.sendmail.call_args.args[2]
    message = message_from_string(raw_message)
    parts = message.get_payload()
    plain_content = parts[0].get_payload(decode=True).decode("utf-8")
    html_content = parts[1].get_payload(decode=True).decode("utf-8")

    assert message.get_content_type() == "multipart/alternative"
    assert [part.get_content_type() for part in parts] == ["text/plain", "text/html"]
    assert "Internal Console" in plain_content
    assert "012345" in plain_content
    assert "有效期至：" in plain_content
    assert "UTC" in plain_content
    assert "Internal Console" in html_content
    assert "012345" in html_content
    assert "此邮件由 Internal Console 系统自动发送" in html_content
    assert "<img" not in html_content
    assert "http://" not in html_content
    assert "https://" not in html_content


def test_email_config_uses_safe_template_defaults(email_utils):
    module, email_config = email_utils

    assert email_config.smtp_server == ""
    assert email_config.smtp_port is None
    assert email_config.sender_email == ""
    assert email_config.sender_password == ""
    assert email_config.sender_name == module.BaseConfig.app_title
    assert email_config.verification_code_expire_seconds == 300
    assert email_config.verification_code_max_attempts == 5
    assert not module.BaseConfig.enable_email_login


def test_send_email_rejects_conflicting_tls_modes(email_utils):
    module, email_config = email_utils
    email_config.smtp_server = "smtp.example.com"
    email_config.smtp_port = 465
    email_config.sender_email = "sender@example.com"
    email_config.sender_password = "smtp-auth-code"
    email_config.smtp_use_ssl = True
    email_config.smtp_use_starttls = True

    with pytest.raises(ValueError, match="不能同时开启"):
        module.send_email_verification_code("recipient@example.com", "012345")
