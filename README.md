<p align="center">
  <img src="./imgs/magic-dash-logo.svg" height="150" alt="magic-dash logo" />
</p>

<h1 align="center">magic-dash</h1>

<p align="center">
  <a href="./setup.py"><img src="https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue" alt="Python" /></a>
  <a href="./LICENSE"><img src="https://shields.io/badge/license-MIT-informational" alt="License" /></a>
  <a href="https://pypi.org/project/magic-dash/"><img src="https://img.shields.io/pypi/v/magic-dash.svg?color=dark-green" alt="PyPI" /></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" /></a>
</p>

`magic-dash` 是面向 Dash 应用开发的命令行脚手架，用于快速生成可运行、可扩展的 Python 数据应用项目。它内置单页面工具、多页面应用和带登录鉴权的管理系统模板，覆盖路由、菜单、配置、回调组织、状态页、数据库模型、用户与权限管理等常见工程起点。

## 快速体验

```bash
pip install magic-dash -U
magic-dash list
magic-dash create --name magic-dash
```

生成项目后：

```bash
cd 生成的项目目录
pip install -r requirements.txt
python app.py
```

`magic-dash-pro` 模板需要先初始化数据库和登录密钥：

```bash
python -m magic_init
python app.py
```

默认访问地址：

```text
http://127.0.0.1:8050
```

## 文档结构

完整入口见 [文档首页](./docs/index.md)。推荐按下面的层次阅读：

### 1. 认识与上手

- [什么是 magic-dash](./docs/what-is-magic-dash.md)
- [快速开始](./docs/quick-start.md)
  - 安装
  - 更新
  - 查看版本
  - 查看内置模板
  - 创建内置模板项目
- [`magic-dash` 命令使用](./docs/cli.md)
  - 安装与版本
  - 查看帮助
  - 查看模板列表
  - 创建项目
  - 错误处理

### 2. 内置模板

- [内置各模板项目介绍](./docs/templates.md)
- [`simple-tool` 模板](./docs/templates.md#simple-tool-模板)
  - 适用场景
  - 创建与启动
  - 目录结构
  - 内置能力
  - 二次开发介绍
    - 单文件改造
    - 拆分 `components/`、`callbacks/`、`utils/`
    - 迁移到多页面模板
  - 详细文档：[`simple-tool` 模板介绍](./docs/simple-tool.md)
- [`magic-dash` 模板](./docs/templates.md#magic-dash-模板)
  - 项目结构
  - 配置参数
    - `BaseConfig`
    - `LayoutConfig`
    - `RouterConfig`
  - 二次开发介绍
    - 新增普通核心页面
    - 新增独立页面
    - 新增通配页面
    - 新增页面回调
  - 详细文档：[`magic-dash` 模板介绍](./docs/magic-dash.md)
- [`magic-dash-pro` 模板](./docs/templates.md#magic-dash-pro-模板)
  - 后端模板
    - [`magic-dash-pro` Flask 后端模板](./docs/magic-dash-pro-flask.md)
    - [`magic-dash-pro` FastAPI 后端模板](./docs/magic-dash-pro-fastapi.md)
  - 项目结构
  - 配置参数
    - `BaseConfig`
    - `LayoutConfig`
    - `RouterConfig`
    - `AuthConfig`
    - `DatabaseConfig`
  - 二次开发介绍
    - 新增受保护普通页面
    - 新增公开页面
    - 新增独立页面
    - 新增通配页面
    - 新增角色与数据库模型
  - 详细文档：[`magic-dash-pro` 模板介绍](./docs/magic-dash-pro.md)

### 3. 配置与二次开发

- [配置参数说明](./docs/configuration.md)
  - `BaseConfig`
  - `LayoutConfig`
  - `RouterConfig`
  - `AuthConfig`
  - `DatabaseConfig`
- [二次开发介绍](./docs/development.md)
  - 开发 `magic-dash` 工具本身
  - 基于 `simple-tool` 二次开发
  - 基于 `magic-dash` 二次开发
  - 基于 `magic-dash-pro` 二次开发

### 4. 反馈与社区

- [问题反馈](./docs/feedback.md)
- [知识社区](./docs/community.md)

## 许可证

本项目基于 [MIT License](./LICENSE) 开源。
