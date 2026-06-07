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

`magic-dash`是面向[Dash](https://github.com/plotly/dash)应用开发的命令行脚手架，用于快速生成可运行、可扩展的`Python`数据应用项目。它内置单页面工具、多页面持续扩展应用和支持复杂用户与部门关系的管理系统模板，覆盖路由、菜单、配置、回调组织、状态页、数据库模型、用户登录、管理与鉴权等常见工程起点。

## 1 快速开始

### 安装&更新

```bash
pip install magic-dash -U
```

查看当前安装版本：

```bash
magic-dash --version
```

### 查看内置模板项目列表

```bash
magic-dash list
```

当前可直接创建的内置模板包括：

- `simple-tool`
- `magic-dash`
- `magic-dash-pro`

### 以magic-dash模板为例创建项目

```bash
magic-dash create --name magic-dash --backend fastapi
```

等价的简写形式为：

```bash
magic-dash create -n magic-dash -b fastapi
```

也可以省略`--backend`或`-b`，通过交互式菜单选择后端类型。随后命令会继续提示输入项目名称，直接回车时，默认生成名为`magic-dash`的项目目录。

### 进入已创建项目，安装依赖并启动应用

```bash
cd magic-dash
pip install -r requirements.txt
python app.py
```

默认访问地址：

```text
http://127.0.0.1:8050
```

更多命令细节见[`CLI`命令说明](./docs/cli.md)。

## 2 内置模板列表

| 模板 | 适用场景 | 子文档入口 |
| --- | --- | --- |
| `simple-tool` | 单页面数据工具、计算器、内部小工具原型 | [项目创建](./docs/simple-tool/项目创建.md) / [二次开发指南](./docs/simple-tool/二次开发指南.md) |
| `magic-dash` | 适用于多页面、持续扩展的[Dash](https://github.com/plotly/dash)应用，内置侧边菜单、路由、状态页和页面组织规范 | [项目创建](./docs/magic-dash/项目创建.md) / [配置参数](./docs/magic-dash/配置参数.md) / [二次开发指南](./docs/magic-dash/二次开发指南.md) |
| `magic-dash-pro` | 适用于多页面、持续扩展的管理型[Dash](https://github.com/plotly/dash)应用，支持复杂用户与部门关系、用户登录、管理和鉴权能力 | [项目创建](./docs/magic-dash-pro/项目创建.md) / [配置参数](./docs/magic-dash-pro/配置参数.md) / [二次开发指南](./docs/magic-dash-pro/二次开发指南.md) |

## 3 反馈和社区

- `GitHub`仓库：[CNFeffery/magic-dash](https://github.com/CNFeffery/magic-dash)
- 问题反馈：[`GitHub Issues`](https://github.com/CNFeffery/magic-dash/issues)
- `PyPI`发布页：[magic-dash](https://pypi.org/project/magic-dash/)
- 作者邮箱：<fefferypzy@gmail.com>

<p align="center">
  <img src="./imgs/公众号.png" alt="公众号二维码" />
  <br />
  <strong>微信公众号</strong>
  <br />
  <sub>关注项目动态与实用教程</sub>
</p>

<p align="center">
  <img src="./imgs/知识星球.jpg" alt="知识星球二维码" />
  <br />
  <strong>知识星球</strong>
  <br />
  <sub>加入社区交流与答疑</sub>
</p>

## 许可证

本项目基于[`MIT License`](./LICENSE)开源。
