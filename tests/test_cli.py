import os
import subprocess
import pytest
from click.testing import CliRunner

import magic_dash as magic_dash_module


class StubPrompt:
    def __init__(self, value):
        self.value = value

    def ask(self):
        return self.value


def select_backend(monkeypatch, backend):
    monkeypatch.setattr(
        magic_dash_module.questionary,
        "select",
        lambda *args, **kwargs: StubPrompt(backend),
    )


def run_command(cmd, input_text=None, env=None):
    """执行命令并返回结果"""
    encoding = "utf-8"
    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    if input_text:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding=encoding,
            errors="replace",
            env=process_env,
        )
        stdout, stderr = process.communicate(input=input_text)
        returncode = process.returncode
    else:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            encoding=encoding,
            errors="replace",
            env=process_env,
        )
        returncode = result.returncode
        stdout = result.stdout or ""
        stderr = result.stderr or ""
    return returncode, stdout, stderr


def test_version():
    """测试版本号查看"""
    returncode, stdout, stderr = run_command("magic-dash --version")
    assert returncode == 0, f"命令执行失败: {stderr}"
    version = stdout.strip()
    assert version, "无版本号输出"
    assert "." in version, f"版本号格式不正确: {version}"


def test_help():
    """测试帮助信息查看"""
    returncode, stdout, stderr = run_command("magic-dash --help")
    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "magic-dash" in stdout.lower(), "帮助信息中未找到程序名"


def test_list():
    """测试 list 命令列出所有内置模板"""
    returncode, stdout, stderr = run_command("magic-dash list")
    assert returncode == 0, f"命令执行失败: {stderr}"

    templates = ["magic-dash", "magic-dash-pro", "simple-tool"]
    for template in templates:
        assert template in stdout, f"未找到模板 '{template}'"

    assert "magic-dash-pro-fastapi" not in stdout, "FastAPI变体不应在顶层模板列表中展示"


@pytest.mark.parametrize("template_name", ["simple-tool", "magic-dash"])
def test_create_with_name(tmp_path, template_name):
    """测试 create 命令创建项目"""
    project_path = tmp_path / template_name

    input_text = "\n"
    returncode, stdout, stderr = run_command(
        f"magic-dash create --name {template_name} --path {tmp_path}",
        input_text=input_text,
    )

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert os.path.exists(project_path), f"项目目录未创建: {project_path}"

    essential_files = ["app.py", "requirements.txt"]
    for file in essential_files:
        assert os.path.exists(os.path.join(project_path, file)), f"{file} 不存在"


def test_create_magic_dash_pro_fastapi_backend(tmp_path, monkeypatch):
    """测试 magic-dash-pro 模板的 FastAPI 后端变体生成"""
    select_backend(monkeypatch, "fastapi")
    project_path = tmp_path / "magic-dash-pro"

    result = CliRunner().invoke(
        magic_dash_module.magic_dash,
        ["create", "--name", "magic-dash-pro", "--path", str(tmp_path)],
        input="\n",
    )

    assert result.exit_code == 0, f"命令执行失败: {result.output}"
    assert os.path.exists(project_path), f"项目目录未创建: {project_path}"

    server_path = os.path.join(project_path, "server.py")
    requirements_path = os.path.join(project_path, "requirements.txt")
    assert os.path.exists(server_path), "server.py 不存在"
    assert os.path.exists(requirements_path), "requirements.txt 不存在"

    with open(server_path, encoding="utf-8") as f:
        server_content = f.read()
    with open(requirements_path, encoding="utf-8") as f:
        requirements_content = f.read()

    assert 'backend="fastapi"' in server_content
    assert "fastapi-login" in requirements_content


def test_create_magic_dash_pro_default_flask_backend(tmp_path, monkeypatch):
    """测试 magic-dash-pro 模板默认使用 Flask 后端"""
    select_backend(monkeypatch, "flask")
    project_path = tmp_path / "magic-dash-pro"

    result = CliRunner().invoke(
        magic_dash_module.magic_dash,
        ["create", "--name", "magic-dash-pro", "--path", str(tmp_path)],
        input="\n",
    )

    assert result.exit_code == 0, f"命令执行失败: {result.output}"
    assert os.path.exists(project_path), f"项目目录未创建: {project_path}"

    with open(os.path.join(project_path, "requirements.txt"), encoding="utf-8") as f:
        requirements_content = f.read()

    assert "Flask_Login" in requirements_content
    assert "fastapi-login" not in requirements_content


def test_create_invalid_name():
    """测试错误处理 - 不存在的模板名称"""
    returncode, stdout, stderr = run_command(
        "magic-dash create --name nonexistent-template"
    )
    assert returncode != 0, "应该返回错误但成功了"


def test_create_fastapi_variant_directly_is_invalid():
    """测试 FastAPI 变体不能作为顶层模板直接选择"""
    returncode, stdout, stderr = run_command(
        "magic-dash create --name magic-dash-pro-fastapi"
    )
    assert returncode != 0, "FastAPI变体不应作为顶层模板直接生成"


def test_create_after_project_name_without_confirm(tmp_path):
    """测试项目名称输入完成后直接创建项目"""
    project_path = tmp_path / "simple-tool"
    input_text = "\n"
    returncode, stdout, stderr = run_command(
        f"magic-dash create --name simple-tool --path {tmp_path}", input_text=input_text
    )

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert os.path.exists(project_path), f"项目目录未创建: {project_path}"
    assert "确认生成项目" not in stdout


def test_create_reprompt_when_project_folder_exists(tmp_path):
    """测试项目名称已存在时提示并重新输入项目名称"""
    existing_path = tmp_path / "simple-tool"
    project_path = tmp_path / "simple-tool-new"
    existing_path.mkdir()

    input_text = "\nsimple-tool-new\n"
    returncode, stdout, stderr = run_command(
        f"magic-dash create --name simple-tool --path {tmp_path}", input_text=input_text
    )

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert os.path.exists(project_path), f"项目目录未创建: {project_path}"
    assert "simple-tool-new" in stdout
