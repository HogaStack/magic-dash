import os
import subprocess
import shutil
import pytest


def run_command(cmd, input_text=None):
    """执行命令并返回结果"""
    encoding = "utf-8"

    if input_text:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding=encoding,
            errors="replace",
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


@pytest.mark.parametrize("template_name", ["simple-tool", "magic-dash"])
def test_create_with_name(tmp_path, template_name):
    """测试 create 命令创建项目"""
    project_path = tmp_path / template_name

    input_text = "\n\n"
    returncode, stdout, stderr = run_command(
        f"magic-dash create --name {template_name} --path {tmp_path}",
        input_text=input_text,
    )

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert os.path.exists(project_path), f"项目目录未创建: {project_path}"

    essential_files = ["app.py", "requirements.txt"]
    for file in essential_files:
        assert os.path.exists(os.path.join(project_path, file)), f"{file} 不存在"


def test_create_invalid_name():
    """测试错误处理 - 不存在的模板名称"""
    returncode, stdout, stderr = run_command(
        "magic-dash create --name nonexistent-template"
    )
    assert returncode != 0, "应该返回错误但成功了"


def test_create_cancel(tmp_path):
    """测试取消创建项目"""
    project_path = tmp_path / "simple-tool"
    input_text = "\nn\n"
    returncode, stdout, stderr = run_command(
        f"magic-dash create --name simple-tool --path {tmp_path}", input_text=input_text
    )

    assert returncode == 0, "取消操作应该正常退出"
    assert not os.path.exists(project_path), "项目不应被创建"
