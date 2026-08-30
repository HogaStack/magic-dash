"""Run one magic-dash-pro template/ORM contract check in an isolated process."""

import importlib
import os
import sys
from datetime import datetime
from pathlib import Path


def check_model_api_contract(template_root: Path, orm_engine: str, workdir: Path):
    os.chdir(workdir)
    sys.path.insert(0, str(template_root))

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

    try:
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
            Users.get_all_users(with_department_name=True)[0]["department_name"]
            == "研发部"
        )

        login_datetime = datetime(2026, 7, 6, 12, 0, 0)
        LoginLogs.add_log(
            "admin",
            "user-1",
            "127.0.0.1",
            "Chrome",
            "Windows",
            "登录成功",
            login_datetime,
        )
        assert LoginLogs.get_count() == 1
        login_log = LoginLogs.get_logs()[0]
        assert login_log["user_name"] == "admin"
        assert isinstance(login_log["login_datetime"], datetime)
        assert login_log["login_datetime"] == login_datetime

        verification, remaining_seconds, previous_verification = (
            EmailVerifications.issue_verification("admin@example.com", 60)
        )
        assert verification.verification_code.isdigit()
        assert remaining_seconds == 0
        assert previous_verification is None

        credential = OtpCredentials.enable_credential("user-1", "secret")
        assert credential.is_enabled
        assert OtpCredentials.has_enabled_otp("user-1")
    finally:
        models.db.close()


if __name__ == "__main__":
    check_model_api_contract(
        template_root=Path(sys.argv[1]).resolve(),
        orm_engine=sys.argv[2],
        workdir=Path(sys.argv[3]).resolve(),
    )
