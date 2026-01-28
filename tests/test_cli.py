import os
import subprocess
import shutil
import pytest
import sys


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
    assert stdout.strip(), "无版本号输出"


def test_list():
    """测试 list 命令列出模板"""
    returncode, stdout, stderr = run_command("magic-dash list")
    assert returncode == 0, f"命令执行失败: {stderr}"
    assert "magic-dash" in stdout, "未找到模板 'magic-dash'"
    assert "simple-tool" in stdout, "未找到模板 'simple-tool'"


def test_create_with_name(tmp_path):
    """测试 create 命令创建项目"""
    project_path = tmp_path / "simple-tool"

    input_text = "\n\n"
    returncode, stdout, stderr = run_command(
        f"magic-dash create --name simple-tool --path {tmp_path}", input_text=input_text
    )

    assert returncode == 0, f"命令执行失败: {stderr}"
    assert os.path.exists(project_path), f"项目目录未创建: {project_path}"
    assert os.path.exists(os.path.join(project_path, "app.py")), "app.py 不存在"


def test_create_invalid_name():
    """测试错误处理 - 不存在的模板名称"""
    returncode, stdout, stderr = run_command(
        "magic-dash create --name nonexistent-template"
    )
    assert returncode != 0, "应该返回错误但成功了"
