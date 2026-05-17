<p align="center">
  <img src="./imgs/logo.svg" height="100" alt="magic-dash logo" />
</p>

<h1 align="center">magic-dash</h1>

<p align="center">
  <a href="./setup.py"><img src="https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue" alt="Python" /></a>
  <a href="./LICENSE"><img src="https://shields.io/badge/license-MIT-informational" alt="License" /></a>
  <a href="https://pypi.org/project/magic-dash/"><img src="https://img.shields.io/pypi/v/magic-dash.svg?color=dark-green" alt="PyPI" /></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" /></a>
</p>

<p align="center">
  面向 <a href="https://github.com/plotly/dash">Dash</a> 应用开发的命令行脚手架，快速生成可运行、可扩展的 Python 数据应用模板。
</p>

`magic-dash` 内置单页面工具、多页面应用和带登录鉴权的管理系统模板，覆盖路由、菜单、配置、回调组织、状态页、数据库模型、用户与权限管理等常见工程起点。

## 快速开始

安装 `magic-dash`：

```bash
pip install magic-dash -U
```

查看当前可生成的模板：

```bash
magic-dash list
```

交互式创建项目：

```bash
magic-dash create
```

指定模板创建项目：

```bash
magic-dash create --name magic-dash
```

指定生成目录：

```bash
magic-dash create --name magic-dash --path ./workspace
```

生成项目后，进入项目目录安装模板依赖并启动：

```bash
cd 生成的项目目录
pip install -r requirements.txt
python app.py
```

`magic-dash-pro` 模板需要先初始化数据库和登录密钥：

```bash
cd 生成的项目目录
pip install -r requirements.txt
python -m models.init_db
python app.py
```

默认访问地址：

```text
http://127.0.0.1:8050
```

`magic-dash-pro` 初始化后的默认管理员账号：

```text
用户名：admin
密码：admin123
```

完整命令说明见 [`magic-dash` 命令使用](./docs/cli.md)。

## 内置模板

| 模板 | 定位 | 典型场景 | 详细文档 |
| --- | --- | --- | --- |
| `simple-tool` | 单页面工具应用模板 | 内部小工具、数据处理表单、快速验证页面 | [查看](./docs/simple-tool.md) |
| `magic-dash` | 基础多页面应用模板 | 多页面后台雏形、数据看板、路由演示项目 | [查看](./docs/magic-dash.md) |
| `magic-dash-pro` | 多页面加登录鉴权管理系统模板 | 用户体系、角色权限、数据库管理后台 | [查看](./docs/magic-dash-pro.md) |

`magic-dash-pro` 会在生成时选择后端类型：

- [`magic-dash-pro` Flask 后端说明](./docs/magic-dash-pro-flask.md)：默认后端，基于 [`flask-login`](https://github.com/maxcountryman/flask-login) 和 [`flask-principal`](https://github.com/mattupstate/flask-principal)。
- [`magic-dash-pro` FastAPI 后端说明](./docs/magic-dash-pro-fastapi.md)：基于 `Dash` 的 `backend="fastapi"` 能力和 [`fastapi-login`](https://github.com/MushroomMaula/fastapi_login)。

## 文档导航

- [`magic-dash` 命令使用](./docs/cli.md)
- [`simple-tool` 模板介绍](./docs/simple-tool.md)
- [`magic-dash` 模板介绍](./docs/magic-dash.md)
- [`magic-dash-pro` 模板介绍](./docs/magic-dash-pro.md)
- [`magic-dash-pro` Flask 后端模板](./docs/magic-dash-pro-flask.md)
- [`magic-dash-pro` FastAPI 后端模板](./docs/magic-dash-pro-fastapi.md)
- [配置参数说明](./docs/configuration.md)
- [二次开发介绍](./docs/development.md)

## 生成项目结构概览

`simple-tool` 生成最小单文件结构：

```text
simple-tool/
├─ app.py
└─ requirements.txt
```

`magic-dash` 生成标准多页面结构：

```text
magic-dash/
├─ assets/
├─ callbacks/
├─ components/
├─ configs/
├─ utils/
├─ views/
├─ server.py
├─ app.py
└─ requirements.txt
```

`magic-dash-pro` 在多页面结构基础上增加鉴权和数据模型：

```text
magic-dash-pro/
├─ assets/
├─ callbacks/
├─ components/
├─ configs/
├─ models/
├─ utils/
├─ views/
├─ server.py
├─ app.py
└─ requirements.txt
```

目录职责、页面扩展和回调组织方式见 [二次开发介绍](./docs/development.md)。

## 配置能力

生成后的 `magic-dash` 系列模板通过 `configs/` 目录集中维护配置：

- `BaseConfig`：应用标题、版本号、浏览器版本限制、更新日志弹窗、登录安全相关配置。
- `LayoutConfig`：侧边栏宽度、核心页面呈现类型、页面搜索、登录页左侧内容类型。
- `RouterConfig`：首页别名、侧边菜单、有效页面、独立页面、通配页面、公开页面。
- `AuthConfig`：`magic-dash-pro` 的角色定义与页面访问规则。
- `DatabaseConfig`：`magic-dash-pro` 的 `SQLite`、`PostgreSQL`、`MySQL` 数据库连接配置。

完整参数表见 [配置参数说明](./docs/configuration.md)。

## 技术栈

`magic-dash` 命令行工具本身使用：

- [`click`](https://github.com/pallets/click)：命令行接口。
- [`questionary`](https://github.com/tmbo/questionary)：交互式选择与确认。
- [`rich`](https://github.com/Textualize/rich)：终端输出美化。
- [`setuptools`](https://github.com/pypa/setuptools)：项目打包。

生成后的应用模板使用：

- [`Dash`](https://github.com/plotly/dash)：应用框架。
- [`feffery-antd-components`](https://github.com/CNFeffery/feffery-antd-components)：基于 `Ant Design` 风格的 `Dash` 组件。
- [`feffery-utils-components`](https://github.com/CNFeffery/feffery-utils-components)：浏览器侧实用组件。
- [`feffery-dash-utils`](https://github.com/CNFeffery/feffery-dash-utils)：版本检查、样式工具等辅助能力。
- [`feffery-markdown-components`](https://github.com/CNFeffery/feffery-markdown-components)：`Markdown` 渲染组件。
- [`peewee`](https://github.com/coleifer/peewee)：`magic-dash-pro` 数据库模型层。
- [`cryptography`](https://github.com/pyca/cryptography)：`magic-dash-pro` 登录密码加密传输相关能力。

## 本地开发与测试

克隆仓库后，可以用可编辑模式安装：

```bash
pip install -e .
```

运行测试：

```bash
pytest
```

当前测试重点覆盖 `magic-dash` 命令行入口、模板列表、模板生成、`magic-dash-pro` 后端选择和非法模板错误处理。更多开发约定见 [二次开发介绍](./docs/development.md)。

## 许可证

本项目基于 [MIT License](./LICENSE) 开源。

## 更多教程

> 微信公众号「玩转 Dash」

<p align="center">
  <img src="./imgs/公众号.png" height="220" alt="玩转 Dash 公众号" />
</p>

> 「玩转 Dash」知识星球

<p align="center">
  <img src="./imgs/知识星球.jpg" height="220" alt="玩转 Dash 知识星球" />
</p>
