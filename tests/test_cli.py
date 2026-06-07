import os
import py_compile
import subprocess
import pytest
from click.testing import CliRunner

import magic_dash as magic_dash_module


class StubPrompt:
    def __init__(self, value):
        self.value = value

    def ask(self):
        return self.value


class StubPromptSequence:
    def __init__(self, values):
        self.values = list(values)

    def __call__(self, *args, **kwargs):
        return StubPrompt(self.values.pop(0))


def select_backend(monkeypatch, backend):
    monkeypatch.setattr(
        magic_dash_module.questionary,
        "select",
        lambda *args, **kwargs: StubPrompt(backend),
    )


def select_sequence(monkeypatch, *values):
    monkeypatch.setattr(
        magic_dash_module.questionary,
        "select",
        StubPromptSequence(values),
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


def assert_backend_created(project_path, template_name, backend):
    dash_file = "app.py" if template_name == "simple-tool" else "server.py"
    dash_path = os.path.join(project_path, dash_file)
    requirements_path = os.path.join(project_path, "requirements.txt")

    assert os.path.exists(project_path), f"项目目录未创建: {project_path}"
    assert os.path.exists(dash_path), f"{dash_file} 不存在"
    assert os.path.exists(requirements_path), "requirements.txt 不存在"

    py_compile.compile(dash_path, doraise=True)

    with open(dash_path, encoding="utf-8") as f:
        dash_content = f.read()
    with open(requirements_path, encoding="utf-8") as f:
        requirements_content = f.read()
    requirements = requirements_content.splitlines()

    if backend == "fastapi":
        assert 'backend="fastapi"' in dash_content
        if template_name == "magic-dash-pro":
            assert "fastapi-login" in requirements_content
        else:
            assert "dash[fastapi]>=4.2.0,<5.0.0" in requirements
            assert "fastapi" in requirements
            assert "uvicorn" in requirements
            assert "flask-compress" not in requirements

        if template_name == "magic-dash":
            assert "from flask import request" not in dash_content
            assert "@app.server.before_request" not in dash_content
            assert '@app.server.middleware("http")' in dash_content
    else:
        assert 'backend="fastapi"' not in dash_content
        assert "fastapi-login" not in requirements_content
        if template_name == "magic-dash-pro":
            assert "Flask_Login" in requirements_content
        else:
            assert "flask-compress" in requirements

        if template_name == "magic-dash":
            assert "from flask import request" in dash_content
            assert "@app.server.before_request" in dash_content


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


def test_create_help_includes_backend_option():
    """测试 create 帮助信息包含后端参数"""
    result = CliRunner().invoke(magic_dash_module.magic_dash, ["create", "--help"])

    assert result.exit_code == 0, f"命令执行失败: {result.output}"
    assert "-n, --name" in result.output
    assert "-p, --path" in result.output
    assert "-b, --backend" in result.output
    assert "--backend" in result.output
    assert "flask" in result.output
    assert "fastapi" in result.output


def test_list():
    """测试 list 命令列出所有内置模板"""
    returncode, stdout, stderr = run_command("magic-dash list")
    assert returncode == 0, f"命令执行失败: {stderr}"

    templates = ["magic-dash", "magic-dash-pro", "simple-tool"]
    for template in templates:
        assert template in stdout, f"未找到模板 '{template}'"

    assert "magic-dash-pro-fastapi" not in stdout, "FastAPI变体不应在顶层模板列表中展示"


@pytest.mark.parametrize("template_name", ["simple-tool", "magic-dash", "magic-dash-pro"])
@pytest.mark.parametrize("backend", ["flask", "fastapi"])
def test_create_with_full_template_backend_options(tmp_path, template_name, backend):
    """测试完整参数指定模板和后端类型创建项目"""
    project_path = tmp_path / template_name

    result = CliRunner().invoke(
        magic_dash_module.magic_dash,
        [
            "create",
            "--name",
            template_name,
            "--path",
            str(tmp_path),
            "--backend",
            backend,
        ],
        input="\n",
    )

    assert result.exit_code == 0, f"命令执行失败: {result.output}"
    assert_backend_created(project_path, template_name, backend)


def test_create_with_short_template_backend_options(tmp_path):
    """测试 create 命令支持短参数形式"""
    project_path = tmp_path / "simple-tool"

    result = CliRunner().invoke(
        magic_dash_module.magic_dash,
        [
            "create",
            "-n",
            "simple-tool",
            "-p",
            str(tmp_path),
            "-b",
            "fastapi",
        ],
        input="\n",
    )

    assert result.exit_code == 0, f"命令执行失败: {result.output}"
    assert_backend_created(project_path, "simple-tool", "fastapi")


@pytest.mark.parametrize("template_name", ["simple-tool", "magic-dash", "magic-dash-pro"])
@pytest.mark.parametrize("backend", ["flask", "fastapi"])
def test_create_interactive_template_and_backend(tmp_path, monkeypatch, template_name, backend):
    """测试交互式选择模板和后端类型创建项目"""
    select_sequence(monkeypatch, template_name, backend)
    project_path = tmp_path / template_name

    result = CliRunner().invoke(
        magic_dash_module.magic_dash,
        ["create", "--path", str(tmp_path)],
        input="\n",
    )

    assert result.exit_code == 0, f"命令执行失败: {result.output}"
    assert_backend_created(project_path, template_name, backend)


def test_create_interactive_template_with_backend_option(tmp_path, monkeypatch):
    """测试交互式选择模板并通过参数指定后端类型"""
    select_sequence(monkeypatch, "magic-dash")
    project_path = tmp_path / "magic-dash"

    result = CliRunner().invoke(
        magic_dash_module.magic_dash,
        ["create", "--path", str(tmp_path), "--backend", "fastapi"],
        input="\n",
    )

    assert result.exit_code == 0, f"命令执行失败: {result.output}"
    assert_backend_created(project_path, "magic-dash", "fastapi")


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


@pytest.mark.parametrize(
    "template_name, dash_file",
    [
        ("simple-tool", "app.py"),
        ("magic-dash", "server.py"),
    ],
)
def test_create_lightweight_template_fastapi_backend(tmp_path, template_name, dash_file):
    """测试轻量模板可在生成后切换为 FastAPI 后端"""
    project_path = tmp_path / template_name

    result = CliRunner().invoke(
        magic_dash_module.magic_dash,
        [
            "create",
            "--name",
            template_name,
            "--path",
            str(tmp_path),
            "--backend",
            "fastapi",
        ],
        input="\n",
    )

    assert result.exit_code == 0, f"命令执行失败: {result.output}"
    assert os.path.exists(project_path), f"项目目录未创建: {project_path}"

    dash_path = os.path.join(project_path, dash_file)
    py_compile.compile(dash_path, doraise=True)

    with open(dash_path, encoding="utf-8") as f:
        dash_content = f.read()
    with open(os.path.join(project_path, "requirements.txt"), encoding="utf-8") as f:
        requirements_content = f.read()
    requirements = requirements_content.splitlines()

    assert 'backend="fastapi"' in dash_content
    assert "dash[fastapi]>=4.2.0,<5.0.0" in requirements
    assert "fastapi" in requirements
    assert "uvicorn" in requirements
    assert "flask-compress" not in requirements

    if template_name == "magic-dash":
        assert "from flask import request" not in dash_content
        assert '@app.server.before_request' not in dash_content
        assert '@app.server.middleware("http")' in dash_content


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
        f"magic-dash create --name simple-tool --path {tmp_path} --backend flask",
        input_text=input_text,
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
        f"magic-dash create --name simple-tool --path {tmp_path} --backend flask",
        input_text=input_text,
    )

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert os.path.exists(project_path), f"项目目录未创建: {project_path}"
    assert "simple-tool-new" in stdout
