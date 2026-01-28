import os
import re
import shutil

import click
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

__version__ = "0.5.0rc2"

# 创建rich console实例
console = Console()

# 现有内置项目模板信息
BUILTIN_TEMPLATES = {
    "magic-dash": {
        "description": "基础多页面应用模板",
    },
    "magic-dash-pro": {
        "description": "多页面+用户登录应用模板",
    },
    "simple-tool": {
        "description": "单页面工具应用模板",
    },
}


@click.group(name="magic-dash")
@click.version_option(version=__version__, message="%(version)s")
def magic_dash():
    """magic-dash命令行工具"""
    pass


@click.command(name="list")
def _list():
    """列出当前可生成的全部Dash应用项目模板"""

    # 创建标题面板
    title = Text("内置Dash应用项目模板", style="bold cyan")
    console.print(Panel(title, border_style="bright_blue", padding=(1, 2)))

    # 创建表格
    table = Table(
        show_header=True, header_style="bold bright_blue", border_style="blue"
    )
    table.add_column("模板名称", style="bold green", width=20)
    table.add_column("模板描述", style="white")

    # 添加模板信息
    for template_name, template_info in BUILTIN_TEMPLATES.items():
        table.add_row(template_name, template_info["description"])

    console.print(table)
    console.print()


@click.command(name="create")
@click.option("--name", type=click.STRING, help="Dash应用项目模板名称")
@click.option("--path", type=click.STRING, default=".", help="项目生成目标路径")
def _create(name, path):
    """生成指定Dash应用项目模板到指定目录"""

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

    # 如果未指定模板名称，显示交互式选择菜单
    if name is None:
        choices = [
            questionary.Choice(
                title=[
                    ("class:highlighted", template_name),
                    ("class:text", f" - {template_info['description']}"),
                ],
                value=template_name,
            )
            for template_name, template_info in BUILTIN_TEMPLATES.items()
        ]

        name = questionary.select(
            "请选择要生成的Dash应用项目模板：",
            choices=choices,
            style=custom_style,
            instruction="(使用方向键选择，回车确认，Esc 取消)",
        ).ask()

        if name is None:
            console.print("\n[yellow bold]已取消项目生成[/yellow bold]\n")
            return

    # 检查目标项目模板是否存在
    if name not in BUILTIN_TEMPLATES.keys():
        error_msg = (
            f"[red][X][/red] [bold]错误：[/bold]不存在的Dash应用项目模板名称 '{name}'"
        )
        console.print(Panel(error_msg, border_style="red", padding=(1, 2)))

        # 显示可用模板
        console.print("\n[yellow]提示：[/yellow] 可用的模板名称：")
        for template in BUILTIN_TEMPLATES.keys():
            console.print(f"  - [cyan]{template}[/cyan]")
        console.print()
        raise click.ClickException("无效的模板名称")

    # 显示模板信息
    template_info = BUILTIN_TEMPLATES[name]
    panel_content = f"[bold]模板名称：[/bold] [cyan]{name}[/cyan]\n[bold]模板描述：[/bold] {template_info['description']}"
    console.print(
        Panel(
            panel_content,
            title="[bold green]准备生成项目[/bold green]",
            border_style="bright_green",
        )
    )

    # 交互式输入配置参数
    console.print(
        "\n[yellow bold]请配置项目参数（直接回车使用默认值）：[/yellow bold]\n"
    )

    # 从命令行交互式输入获取项目名称
    project_name = click.prompt(
        "项目名称", default=name, type=click.STRING, show_default=True
    )

    # 显示生成信息
    console.print(f"\n[bold]目标路径：[/bold] [cyan]{path}[/cyan]")
    console.print(f"[bold]项目名称：[/bold] [cyan]{project_name}[/cyan]")

    # 确认生成
    console.print()
    console.print("[dim]（输入 y 确认，输入 n 取消，直接回车使用默认选项 Y）[/dim]")
    if not click.confirm("确认生成项目？", default=True):
        console.print("\n[yellow bold]已取消项目生成[/yellow bold]\n")
        return

    # 生成项目
    console.print("\n[cyan]正在生成项目...[/cyan]")

    # 复制项目模板到指定目录
    shutil.copytree(
        src=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "templates",
            name,
        ),
        dst=os.path.join(path, name),
    )

    # 替换版本号
    base_config_path = os.path.join(path, name, "configs", "base_config.py")
    if os.path.exists(base_config_path):
        with open(base_config_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(
            r'app_version: str = "[^"]*"',
            f'app_version: str = "{__version__}"',
            content,
        )
        with open(base_config_path, "w", encoding="utf-8") as f:
            f.write(content)

    # 重命名项目
    os.rename(
        src=os.path.join(path, name),
        dst=os.path.join(path, project_name),
    )

    # 显示成功信息
    success_msg = (
        f"[bold green][√][/bold green] [bold]已成功生成项目[/bold] [cyan]{project_name}[/cyan]\n"
        f"[bold]项目路径：[/bold] {os.path.join(path, project_name)}\n\n"
        f"[dim]提示：[/dim] 进入项目目录后，可以运行以下命令启动应用：\n"
        f"  [dim]-[/dim] [cyan]cd {project_name}[/cyan]\n"
        f"  [dim]-[/dim] [cyan]pip install -r requirements.txt[/cyan]"
    )

    # 如果是magic-dash-pro模板，需要初始化数据库
    if name == "magic-dash-pro":
        success_msg += "\n  [dim]-[/dim] [cyan]python -m models.init_db[/cyan]"

    success_msg += "\n  [dim]-[/dim] [cyan]python app.py[/cyan]"

    console.print(
        Panel(
            success_msg,
            title="[bold green]项目生成成功[/bold green]",
            border_style="bright_green",
            padding=(1, 2),
        )
    )


# 令子命令生效
magic_dash.add_command(_list)
magic_dash.add_command(_create)

if __name__ == "__main__":
    magic_dash()
