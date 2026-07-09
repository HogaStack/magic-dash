import os

import questionary
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from werkzeug.security import generate_password_hash

from configs import AuthConfig, BaseConfig
from models import (
    create_tables,
    db,  # noqa: F401
    ensure_user_email_schema as ensure_model_user_email_schema,
    get_model_table_name,
    model_table_exists,
    model_table_has_data,
)
from models.departments import Departments
from models.email_verifications import EmailVerifications
from models.otp_credentials import OtpCredentials
from models.user_permission_groups import UserPermissionGroups
from models.users import Users
from utils.validation_utils import validate_optional_email

# 创建rich console实例
console = Console()

BUILTIN_DATABASE_TABLES = [
    ("用户信息表", Users, "用户账号、角色、部门归属与登录会话"),
    ("部门信息表", Departments, "组织部门层级与扩展信息"),
    ("用户权限分组表", UserPermissionGroups, "用户角色分组与页面访问规则"),
    ("邮箱验证码信息表", EmailVerifications, "邮箱登录/绑定验证码记录"),
    ("用户OTP动态口令凭据表", OtpCredentials, "用户TOTP二次验证凭据"),
]


def generate_rsa_key_pair():
    """生成RSA密钥对并保存到项目根目录"""

    private_key_path = BaseConfig.rsa_private_key_path
    public_key_path = BaseConfig.rsa_public_key_path

    # 生成RSA密钥对
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # 序列化私钥
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # 序列化公钥
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # 保存到文件
    with open(private_key_path, "wb") as f:
        f.write(private_pem)

    with open(public_key_path, "wb") as f:
        f.write(public_pem)


def check_rsa_keys_exist():
    """检查RSA密钥对文件是否已存在"""

    return os.path.exists(BaseConfig.rsa_private_key_path) and os.path.exists(
        BaseConfig.rsa_public_key_path
    )


def check_table_exists(table_model):
    """检查数据表是否已存在"""

    return model_table_exists(table_model)


def check_table_has_data(table_model):
    """检查数据表是否已有数据"""

    return model_table_has_data(table_model)


def get_builtin_table_creation_records(table_exists_map):
    """获取内置数据表创建记录。"""

    return [
        {
            "label": label,
            "table_name": get_model_table_name(table_model),
            "description": description,
            "created": not table_exists_map[table_model],
        }
        for label, table_model, description in BUILTIN_DATABASE_TABLES
    ]


def print_builtin_table_creation_records(table_creation_records):
    """打印内置数据表创建记录清单。"""

    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="bright_blue",
        expand=True,
    )
    table.add_column("序号", justify="right", style="dim", no_wrap=True, width=4)
    table.add_column("内置数据表", style="yellow", no_wrap=True)
    table.add_column("物理表名", style="cyan", no_wrap=True)
    table.add_column("创建记录", no_wrap=True)

    for index, record in enumerate(table_creation_records, 1):
        status = (
            "[green]已创建[/green]"
            if record["created"]
            else "[dim]已存在，跳过创建[/dim]"
        )
        table.add_row(
            str(index),
            record["label"],
            record["table_name"],
            status,
        )

    console.print("\n")
    console.print(
        Panel(
            table,
            title="[bold cyan]内置数据表创建记录[/bold cyan]",
            subtitle="[dim]magic_init[/dim]",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )


def ensure_user_email_schema():
    """通过models层统一处理用户邮箱字段与唯一约束兼容逻辑"""

    return ensure_model_user_email_schema(Users)


def ask_admin_email():
    """询问初始管理员邮箱，直接回车则跳过"""

    while True:
        value = questionary.text(
            "初始管理员邮箱（可选）：",
            style=custom_style,
        ).ask()

        value = (value or "").strip()

        if validate_optional_email(value):
            return value or None

        console.print("[red]邮箱格式不正确[/red]")


# 统一的questionary样式
custom_style = questionary.Style(
    [
        ("qmark", "fg:#FFD700 bold"),
        ("question", "bold cyan"),
        ("answer", "bold green"),
        ("pointer", "fg:#FFD700 bold"),
        ("highlighted", "fg:#00FFFF bold"),
        ("selected", "fg:#00FF00 bold"),
        ("instruction", "fg:#888"),
    ]
)


def main():
    """初始化magic-dash-pro项目所需的数据库与安全密钥。"""

    # 显示标题面板
    title = Text("项目初始化工具", style="bold cyan")
    subtitle = Text("magic-dash-pro", style="dim")
    console.print(
        Panel(title, subtitle=subtitle, border_style="bright_blue", padding=(1, 2))
    )

    # 预先检查内置数据表是否已存在
    table_exists_map = {
        table_model: check_table_exists(table_model)
        for _, table_model, _ in BUILTIN_DATABASE_TABLES
    }
    departments_exists = table_exists_map[Departments]
    users_exists = table_exists_map[Users]

    # 记录执行结果和管理员信息
    executed_operations = []
    admin_created = False
    admin_email = None

    # 创建表（如果表不存在）
    create_tables([table_model for _, table_model, _ in BUILTIN_DATABASE_TABLES])
    print_builtin_table_creation_records(
        get_builtin_table_creation_records(table_exists_map)
    )

    # 兼容旧版本已存在的用户信息表
    for operation in ensure_user_email_schema():
        executed_operations.append((operation, "已自动补充", "yellow", "green"))

    # 0. RSA密钥对生成
    if BaseConfig.enable_login_rsa_crypto:
        # 检查是否已存在RSA密钥对
        if check_rsa_keys_exist():
            # 已存在密钥，询问是否覆盖
            console.print("\n[dim]请确认以下安全密钥操作：[/dim]\n")
            confirm_override = questionary.confirm(
                f"检测到已存在RSA密钥对文件（{BaseConfig.rsa_private_key_path} 和 {BaseConfig.rsa_public_key_path}），是否重新生成并覆盖？",
                default=False,
                style=custom_style,
            ).ask()

            if confirm_override:
                try:
                    generate_rsa_key_pair()
                    executed_operations.append(
                        (
                            "RSA密钥对",
                            f"已重新生成并覆盖\n    私钥: {BaseConfig.rsa_private_key_path}\n    公钥: {BaseConfig.rsa_public_key_path}",
                            "yellow",
                            "green",
                        )
                    )
                except Exception as e:
                    executed_operations.append(
                        ("RSA密钥对", f"重新生成失败: {str(e)}", "yellow", "red")
                    )
            else:
                executed_operations.append(
                    (
                        "RSA密钥对",
                        f"保留现有密钥文件\n    私钥: {BaseConfig.rsa_private_key_path}\n    公钥: {BaseConfig.rsa_public_key_path}",
                        "dim",
                        "dim",
                    )
                )
        else:
            # 不存在密钥，直接生成
            console.print(
                "\n[dim]检测到当前项目根目录中不存在RSA密钥对文件，正在自动生成...[/dim]"
            )
            try:
                generate_rsa_key_pair()
                executed_operations.append(
                    (
                        "RSA密钥对",
                        f"已自动生成\n    私钥: {BaseConfig.rsa_private_key_path}\n    公钥: {BaseConfig.rsa_public_key_path}",
                        "yellow",
                        "green",
                    )
                )
            except Exception as e:
                executed_operations.append(
                    ("RSA密钥对", f"生成失败: {str(e)}", "yellow", "red")
                )
    else:
        executed_operations.append(
            ("RSA密钥对", "已跳过（未开启登录密码RSA加密）", "dim", "dim")
        )

    # 1&2. 检查部门和用户表数据状态
    departments_has_data = departments_exists and check_table_has_data(Departments)
    users_has_data = users_exists and check_table_has_data(Users)

    # 判断是否需要用户交互（表存在且有数据时需要询问）
    need_user_confirm = (departments_exists and departments_has_data) or (
        users_exists and users_has_data
    )

    if need_user_confirm:
        console.print("\n[dim]请确认以下数据库操作：[/dim]\n")

    # 处理部门信息表
    if departments_exists and departments_has_data:
        # 表存在且有数据，询问是否重置
        confirm_departments = questionary.confirm(
            "重置部门信息表？（Enter 跳过）",
            default=False,
            style=custom_style,
        ).ask()

        if confirm_departments:
            try:
                Departments.truncate_departments(execute=True)
                executed_operations.append(("部门信息表", "已重置", "yellow", "green"))
            except Exception as e:
                executed_operations.append(
                    ("部门信息表", f"重置失败: {str(e)}", "yellow", "red")
                )
        else:
            executed_operations.append(("部门信息表", "已跳过", "dim", "dim"))
    else:
        # 表不存在或没有数据，跳过（表已在顶部创建）
        if not departments_exists:
            executed_operations.append(("部门信息表", "已自动创建", "yellow", "green"))
        else:
            executed_operations.append(("部门信息表", "表已存在但无数据", "dim", "dim"))

    # 处理用户信息表
    if users_exists and users_has_data:
        # 表存在且有数据，询问是否重置
        confirm_users = questionary.confirm(
            "重置用户信息表并初始化管理员账号？（Enter 跳过）",
            default=False,
            style=custom_style,
        ).ask()

        if confirm_users:
            try:
                console.print("\n[dim]初始管理员账号[/dim]\n")
                admin_email = ask_admin_email()
                Users.truncate_users(execute=True)

                # 初始化管理员用户
                Users.add_user(
                    user_id="admin",
                    user_name="admin",
                    password_hash=generate_password_hash("admin123"),
                    user_email=admin_email,
                    user_role=AuthConfig.admin_role,
                )

                admin_created = True
                executed_operations.append(
                    ("用户信息表", "已重置 + 管理员初始化", "yellow", "green")
                )
            except Exception as e:
                executed_operations.append(
                    ("用户信息表", f"重置失败: {str(e)}", "yellow", "red")
                )
        else:
            executed_operations.append(("用户信息表", "已跳过", "dim", "dim"))
    else:
        # 表不存在或没有数据，自动初始化
        try:
            console.print("\n[dim]初始管理员账号[/dim]\n")
            admin_email = ask_admin_email()

            if users_exists:
                Users.truncate_users(execute=True)

            # 初始化管理员用户
            Users.add_user(
                user_id="admin",
                user_name="admin",
                password_hash=generate_password_hash("admin123"),
                user_email=admin_email,
                user_role=AuthConfig.admin_role,
            )

            admin_created = True
            if not users_exists:
                executed_operations.append(
                    ("用户信息表", "已自动创建 + 管理员初始化", "yellow", "green")
                )
            else:
                executed_operations.append(
                    ("用户信息表", "已自动初始化管理员账号", "yellow", "green")
                )
        except Exception as e:
            executed_operations.append(
                ("用户信息表", f"初始化失败: {str(e)}", "yellow", "red")
            )

    # 显示操作结果汇总
    console.print("\n")
    result_text = Text()
    for i, (table, status, table_style, status_style) in enumerate(
        executed_operations, 1
    ):
        result_text.append(f"  {i}. ", style="dim")
        result_text.append(f"{table}: ", style=table_style)
        result_text.append(f"{status}\n", style=status_style)

    # 如果有管理员账号创建，在汇总中添加账号信息
    if admin_created:
        result_text.append("\n", style="default")
        result_text.append("  初始管理员账号", style="cyan")
        result_text.append(":\n", style="default")
        result_text.append("     用户名: ", style="dim")
        result_text.append("admin\n", style="yellow bold")
        result_text.append("     初始密码: ", style="dim")
        result_text.append("admin123\n", style="yellow bold")
        if admin_email:
            result_text.append("     邮箱: ", style="dim")
            result_text.append(f"{admin_email}\n", style="yellow bold")
        else:
            result_text.append("     邮箱: ", style="dim")
            result_text.append("未设置\n", style="dim")

    console.print(
        Panel(
            result_text,
            title="[bold green]\u2713 操作完成[/bold green]",
            border_style="bright_green",
            padding=(1, 2),
        )
    )


if __name__ == "__main__":
    main()
