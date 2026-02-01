import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from werkzeug.security import generate_password_hash

from models import db

# 导入相关数据表模型
from .users import Users
from .departments import Departments
from configs import AuthConfig

# 创建rich console实例
console = Console()

# 创建表（如果表不存在）
db.create_tables([Users, Departments])

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


if __name__ == "__main__":
    # 显示标题面板
    title = Text("数据库初始化工具", style="bold cyan")
    subtitle = Text("magic-dash-pro", style="dim")
    console.print(
        Panel(title, subtitle=subtitle, border_style="bright_blue", padding=(1, 2))
    )

    # 记录执行结果和管理员信息
    executed_operations = []
    admin_created = False

    # 1. 询问是否重置部门表
    console.print("\n[dim]请确认以下数据库操作：[/dim]\n")
    confirm_departments = questionary.confirm(
        "是否重置部门信息表？",
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

    # 2. 询问是否重置用户表
    confirm_users = questionary.confirm(
        "是否重置用户信息表？",
        default=False,
        style=custom_style,
    ).ask()

    if confirm_users:
        try:
            Users.truncate_users(execute=True)

            # 初始化管理员用户
            Users.add_user(
                user_id="admin",
                user_name="admin",
                password_hash=generate_password_hash("admin123"),
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

    console.print(
        Panel(
            result_text,
            title="[bold green]\u2713 操作完成[/bold green]",
            border_style="bright_green",
            padding=(1, 2),
        )
    )
