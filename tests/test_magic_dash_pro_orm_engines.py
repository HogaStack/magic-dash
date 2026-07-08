import importlib
import sys
from pathlib import Path

import pytest


TEMPLATE_ROOT = (
    Path(__file__).resolve().parents[1] / "magic_dash" / "templates" / "magic-dash-pro"
)


def clear_template_modules():
    for module_name in list(sys.modules):
        if module_name == "models" or module_name.startswith("models."):
            sys.modules.pop(module_name)
        elif module_name == "configs" or module_name.startswith("configs."):
            sys.modules.pop(module_name)


@pytest.mark.parametrize("orm_engine", ["sqlalchemy", "sqlmodel"])
def test_magic_dash_pro_alternative_engine_keeps_model_api_contract(
    tmp_path,
    monkeypatch,
    orm_engine,
):
    clear_template_modules()
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(TEMPLATE_ROOT))

    engine_package = f"models._{orm_engine}"
    models = importlib.import_module(engine_package)
    Users = importlib.import_module(f"{engine_package}.users").Users
    Departments = importlib.import_module(f"{engine_package}.departments").Departments
    LoginLogs = importlib.import_module(f"{engine_package}.logs").LoginLogs
    EmailVerifications = importlib.import_module(
        f"{engine_package}.email_verifications"
    ).EmailVerifications
    OtpCredentials = importlib.import_module(
        f"{engine_package}.otp_credentials"
    ).OtpCredentials
    UserPermissionGroups = importlib.import_module(
        f"{engine_package}.user_permission_groups"
    ).UserPermissionGroups

    models.create_tables(
        [
            Users,
            Departments,
            LoginLogs,
            EmailVerifications,
            OtpCredentials,
            UserPermissionGroups,
        ]
    )

    Departments.add_department("dept-1", "研发部")
    assert Departments.get_department("dept-1").department_name == "研发部"
    assert Departments.get_all_departments()[0]["department_id"] == "dept-1"

    assert UserPermissionGroups.get_all_permission_groups() == []
    Users.add_user(
        "user-1",
        "admin",
        "password-hash",
        user_email="admin@example.com",
        department_id="dept-1",
        user_role="normal",
    )
    assert Users.get_user("user-1").user_name == "admin"
    assert Users.get_user_by_email("admin@example.com").user_id == "user-1"
    assert (
        Users.get_all_users(with_department_name=True)[0]["department_name"] == "研发部"
    )

    LoginLogs.add_log(
        "admin",
        "user-1",
        "127.0.0.1",
        "Chrome",
        "Windows",
        "登录成功",
        "2026-07-06 12:00:00",
    )
    assert LoginLogs.get_count() == 1
    assert LoginLogs.get_logs()[0]["user_name"] == "admin"
    assert LoginLogs.get_logs()[0]["login_datetime"] == "2026-07-06 12:00:00"

    verification, remaining_seconds, previous_verification = (
        EmailVerifications.issue_verification("admin@example.com", 60)
    )
    assert verification.verification_code.isdigit()
    assert remaining_seconds == 0
    assert previous_verification is None

    credential = OtpCredentials.enable_credential("user-1", "secret")
    assert credential.is_enabled
    assert OtpCredentials.has_enabled_otp("user-1")

    models.db.close()
    clear_template_modules()
