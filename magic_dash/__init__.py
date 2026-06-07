import os
import re
import shutil

import click
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

__version__ = "0.5.0"


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

PRO_BACKEND_TEMPLATES = {
    "flask": "magic-dash-pro",
    "fastapi": "magic-dash-pro-fastapi",
}

BACKEND_SELECT_TEMPLATES = {
    "magic-dash",
    "magic-dash-pro",
    "simple-tool",
}

LIGHTWEIGHT_BACKEND_TEMPLATES = {
    "magic-dash",
    "simple-tool",
}

FASTAPI_REQUIREMENTS = [
    "fastapi",
    "uvicorn",
]


def _normalize_backend_name(backend):
    if backend is None:
        return None

    return backend.lower()


def _select_backend(template_name, custom_style, backend=None):
    backend = _normalize_backend_name(backend)
    if backend:
        return backend

    backend_choices = [
        questionary.Choice(
            title=[
                ("class:highlighted", "Flask"),
                ("class:text", " - 默认后端"),
            ],
            value="flask",
        ),
        questionary.Choice(
            title=[
                ("class:highlighted", "FastAPI"),
                ("class:text", " - 适用于FastAPI后端基底"),
            ],
            value="fastapi",
        ),
    ]

    normalized_backend_name = questionary.select(
        f"请选择{template_name}模板后端类型：",
        choices=backend_choices,
        default="flask",
        style=custom_style,
        instruction="(使用方向键选择，回车确认，Esc 取消)",
    ).ask()

    if normalized_backend_name is None:
        console.print("\n[yellow bold]已取消项目生成[/yellow bold]\n")
        return None

    return normalized_backend_name


def _ensure_fastapi_requirements(project_path):
    requirements_path = os.path.join(project_path, "requirements.txt")
    if not os.path.exists(requirements_path):
        return

    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = f.read().splitlines()

    updated_requirements = []
    has_dash = False
    existing_packages = set()

    for line in requirements:
        stripped_line = line.strip()
        package_name = re.split(r"[<>=!~\[]", stripped_line, maxsplit=1)[0].lower()
        if package_name:
            existing_packages.add(package_name)

        if re.match(r"^dash([<>=!~]|\[)", stripped_line):
            updated_requirements.append(
                re.sub(r"^dash(?:\[[^\]]+\])?", "dash[fastapi]", line)
            )
            has_dash = True
            continue

        if package_name == "flask-compress":
            continue

        updated_requirements.append(line)

    if not has_dash:
        updated_requirements.insert(0, "dash[fastapi]>=4.2.0,<5.0.0")

    for requirement in FASTAPI_REQUIREMENTS:
        if requirement.lower() not in existing_packages:
            updated_requirements.append(requirement)

    with open(requirements_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(updated_requirements).rstrip() + "\n")


def _enable_fastapi_dash_backend(project_path):
    for root, _, files in os.walk(project_path):
        for filename in files:
            if not filename.endswith(".py"):
                continue

            file_path = os.path.join(root, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if "dash.Dash(" not in content or 'backend="fastapi"' in content:
                continue

            updated_content = re.sub(
                r"(dash\.Dash\(\s*__name__,)",
                r'\1\n    backend="fastapi",',
                content,
                count=1,
            )

            if updated_content == content:
                continue

            with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(updated_content)


def _convert_magic_dash_server_to_fastapi(project_path):
    server_path = os.path.join(project_path, "server.py")
    if not os.path.exists(server_path):
        return

    with open(server_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "from flask import request" not in content:
        return

    content = content.replace(
        "from flask import request",
        "from fastapi import Request\nfrom fastapi.responses import HTMLResponse",
    )

    middleware = '''def _browser_block_message(request: Request):
    """检查浏览器版本是否符合最低要求"""

    user_agent = parse(request.headers.get("user-agent", ""))

    if user_agent.browser.version == ():
        return None

    if user_agent.browser.family == "IE":
        return (
            "<div style='font-size: 16px; color: red; position: fixed; top: 40%; left: 50%; transform: translateX(-50%);'>"
            "请不要使用IE浏览器，或开启了IE内核兼容模式的其他浏览器访问本应用</div>"
        )

    for rule in BaseConfig.min_browser_versions:
        if (
            user_agent.browser.family == rule["browser"]
            and user_agent.browser.version[0] < rule["version"]
        ):
            return (
                "<div style='font-size: 16px; color: red; position: fixed; top: 40%; left: 50%; transform: translateX(-50%);'>"
                "您的{}浏览器版本低于本应用最低支持版本（{}），请升级浏览器后再访问</div>"
            ).format(rule["browser"], rule["version"])

    if BaseConfig.strict_browser_type_check:
        if user_agent.browser.family not in [
            rule["browser"] for rule in BaseConfig.min_browser_versions
        ]:
            return (
                "<div style='font-size: 16px; color: red; position: fixed; top: 40%; left: 50%; transform: translateX(-50%);'>"
                "当前浏览器类型不在支持的范围内，支持的浏览器类型有：{}</div>"
            ).format(
                "、".join(
                    [rule["browser"] for rule in BaseConfig.min_browser_versions]
                )
            )

    return None


@app.server.middleware("http")
async def check_browser(request: Request, call_next):
    browser_block_message = _browser_block_message(request)
    if browser_block_message:
        return HTMLResponse(browser_block_message)

    return await call_next(request)
'''

    content = re.sub(
        r"\n\n@app\.server\.before_request\ndef check_browser\(\):.*\Z",
        "\n\n" + middleware,
        content,
        flags=re.S,
    )

    with open(server_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def _apply_lightweight_fastapi_backend(project_path, template_name):
    _ensure_fastapi_requirements(project_path)
    _enable_fastapi_dash_backend(project_path)

    if template_name == "magic-dash":
        _convert_magic_dash_server_to_fastapi(project_path)


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
@click.option("-n", "--name", type=click.STRING, help="Dash应用项目模板名称")
@click.option("-p", "--path", type=click.STRING, default=".", help="项目生成目标路径")
@click.option(
    "-b",
    "--backend",
    type=click.Choice(["flask", "fastapi"], case_sensitive=False),
    help="Dash应用项目后端类型",
)
def _create(name, path, backend):
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

    source_template_name = name
    project_default_name = name

    normalized_backend_name = "flask"
    if name in BACKEND_SELECT_TEMPLATES:
        normalized_backend_name = _select_backend(name, custom_style, backend)

        if normalized_backend_name is None:
            return

        if name == "magic-dash-pro":
            source_template_name = PRO_BACKEND_TEMPLATES[normalized_backend_name]

        backend_name = "FastAPI" if normalized_backend_name == "fastapi" else "Flask"
        console.print(f"[bold]后端类型：[/bold] [cyan]{backend_name}[/cyan]")

    while True:
        # 从命令行交互式输入获取项目名称
        project_name = click.prompt(
            "项目名称",
            default=project_default_name,
            type=click.STRING,
            show_default=True,
        )
        project_path = os.path.join(path, project_name)

        if not os.path.exists(project_path):
            break

        console.print(
            f"[yellow]目标路径下已存在同名文件夹[/yellow] [cyan]{project_name}[/cyan]，"
            "请重新输入项目名称。"
        )
        project_default_name = project_name

    # 显示生成信息
    console.print(f"\n[bold]目标路径：[/bold] [cyan]{path}[/cyan]")
    console.print(f"[bold]项目名称：[/bold] [cyan]{project_name}[/cyan]")

    # 生成项目
    console.print("\n[cyan]正在生成项目...[/cyan]")

    # 复制项目模板到指定目录
    shutil.copytree(
        src=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "templates",
            source_template_name,
        ),
        dst=project_path,
    )

    if (
        name in LIGHTWEIGHT_BACKEND_TEMPLATES
        and normalized_backend_name == "fastapi"
    ):
        _apply_lightweight_fastapi_backend(project_path, name)

    # 替换版本号 (仅 magic-dash 系列模板)
    if source_template_name in (
        "magic-dash",
        "magic-dash-pro",
        "magic-dash-pro-fastapi",
    ):
        base_config_path = os.path.join(project_path, "configs", "base_config.py")
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
        success_msg += "\n  [dim]-[/dim] [cyan]python -m magic_init[/cyan]"

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
