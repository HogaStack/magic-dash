import os
import re
import click
import shutil

__version__ = "0.5.0rc2"

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
    click.echo("内置Dash应用项目模板：\n")
    # 为magic-dash输出添加高亮颜色
    for template in BUILTIN_TEMPLATES.keys():
        click.echo(
            click.style(
                "- {}    {}".format(
                    template, BUILTIN_TEMPLATES[template]["description"]
                ),
                fg="bright_yellow",
            )
        )


@click.command(name="create")
@click.option("--name", required=True, type=click.STRING, help="Dash应用项目模板名称")
@click.option("--path", type=click.STRING, default=".", help="项目生成目标路径")
def _create(name, path):
    """生成指定Dash应用项目模板到指定目录"""

    # 检查目标项目模板是否存在
    if name not in BUILTIN_TEMPLATES.keys():
        click.echo(
            click.style(
                "不存在的Dash应用项目模板名称：{}".format(name),
                fg="red",
            )
        )
        return

    # 交互式输入配置参数
    click.echo(
        click.style(
            "\n请配置项目参数（直接回车使用默认值）：\n",
            fg="yellow",
        )
    )

    # 从命令行交互式输入获取项目名称
    project_name = click.prompt(
        "项目名称", default=name, type=click.STRING, show_default=True
    )

    # 复制项目模板到指定目录
    shutil.copytree(
        src=os.path.join(
            # magic-dash实际位置
            os.path.dirname(os.path.abspath(__file__)),
            "templates",
            name,
        ),
        dst=os.path.join(path, name),
    )

    # 替换模板中的版本号（仅修改base_config.py）
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

    # 重命名已生成项目名称
    os.rename(
        src=os.path.join(path, name),
        dst=os.path.join(path, project_name),
    )

    click.echo(
        click.style(
            "已成功生成项目 {} 至目录 {}".format(
                name, os.path.join(path, project_name)
            ),
            fg="green",
        )
    )


# 令子命令生效
magic_dash.add_command(_list)
magic_dash.add_command(_create)

if __name__ == "__main__":
    magic_dash()
