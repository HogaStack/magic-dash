<p align="center">
	<img src="./imgs/logo.svg" height=100></img>
</p>
<h1 align="center">magic-dash</h1>
<div align="center">

[![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](./setup.py)
[![GitHub](https://shields.io/badge/license-MIT-informational)](https://github.com/CNFeffery/magic-dash/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/magic-dash.svg?color=dark-green)](https://pypi.org/project/magic-dash/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

</div>

命令行工具，用于快捷生成一系列开箱即用✨的标准[Dash](https://github.com/plotly/dash)应用工程模板，加速你的应用开发进程🚀。

`magic-dash` 适合在开始一个新的 Dash 项目时快速搭好目录、路由、页面骨架、配置文件、静态资源、常用回调组织方式，以及用户登录/权限/数据库等可选能力。生成后的项目是普通 Python 工程，可继续按业务需求自由二次开发。

## 目录

[1 安装](#install)<br>
[2 快速使用](#usage)<br>
[3 内置模板列表](#template-list)<br>
[4 生成项目通用结构](#project-structure)<br>
[5 模板配置与二次开发说明](#template-guide)<br>
[6 更新日志](#changelog)<br>
[7 更多应用开发教程](#courses)<br>

<a name="install" ></a>

## 1 安装

```bash
pip install magic-dash -U
```

项目生成后，每个模板目录内都会包含独立的 `requirements.txt`，进入生成后的项目目录后再安装对应依赖：

```bash
pip install -r requirements.txt
```

<a name="usage" ></a>

## 2 快速使用

### 2.1 查看内置项目模板

```bash
magic-dash list
```

当前顶层可选模板包括：

```bash
- magic-dash       基础多页面应用模板
- magic-dash-pro   多页面+用户登录应用模板
- simple-tool      单页面工具应用模板
```

其中 `magic-dash-pro` 会在生成过程中继续询问后端类型，可选择默认 `Flask` 后端或 `FastAPI` 后端；`magic-dash-pro-fastapi` 是内部隐藏模板，不会直接出现在 `magic-dash list` 中，也不能作为顶层模板名称直接生成。

### 2.2 交互式生成项目

不指定 `--name` 时，会进入模板选择菜单：

```bash
magic-dash create
```

### 2.3 生成指定模板

```bash
magic-dash create --name magic-dash
```

指定生成路径：

```bash
magic-dash create --name magic-dash --path 目标路径
```

生成 `magic-dash-pro` 时，会额外选择后端类型：

```bash
magic-dash create --name magic-dash-pro
```

在后端类型单选菜单中直接回车使用默认 `Flask` 后端；使用方向键选择 `FastAPI` 后回车，则生成 FastAPI 后端版本。

### 2.4 启动生成后的应用

基础模板和单页工具模板：

```bash
cd 项目目录
pip install -r requirements.txt
python app.py
```

`magic-dash-pro` 模板需要先初始化数据库：

```bash
cd 项目目录
pip install -r requirements.txt
python -m models.init_db
python app.py
```

默认访问地址：

```bash
http://127.0.0.1:8050
```

`magic-dash-pro` 初始化后内置管理员账号：

```bash
用户名：admin
密码：admin123
```

### 2.5 查看命令说明

```bash
magic-dash --version
magic-dash --help
magic-dash list --help
magic-dash create --help
```

<a name="template-list" ></a>

## 3 内置模板列表

| 模板名称 | 适用场景 | 核心能力 | 说明文档 |
| :-- | :-- | :-- | :-- |
| `simple-tool` | 单页面小工具、数据处理页面、内部辅助工具 | 一个 `app.py` 起步，结构极简 | [查看](./docs/simple-tool.md) |
| `magic-dash` | 常规多页面应用、后台系统雏形、路由演示项目 | 多页面路由、侧边菜单、状态页、独立页面、通配页面、浏览器回调组织 | [查看](./docs/magic-dash.md) |
| `magic-dash-pro` | 带用户登录、权限、用户管理、部门管理和登录日志的管理系统 | `magic-dash` 能力 + 登录鉴权 + 数据库模型 + RSA 登录密码加密 + 管理模块 | [查看](./docs/magic-dash-pro.md) |

<a name="project-structure" ></a>

## 4 生成项目通用结构

### 4.1 `simple-tool`

```bash
simple-tool
 ┣ app.py              # 应用主文件
 ┗ requirements.txt    # 项目依赖信息
```

### 4.2 `magic-dash`

```bash
magic-dash
 ┣ assets              # 静态资源目录
 ┃ ┣ css               # 样式文件
 ┃ ┣ imgs              # 图片资源
 ┃ ┣ js                # 浏览器端回调函数
 ┃ ┗ favicon.ico       # 网页图标
 ┣ callbacks           # Dash回调函数模块
 ┣ components          # 可复用页面组件模块
 ┣ configs             # 配置参数模块
 ┣ utils               # 工具函数模块
 ┣ views               # 页面模块
 ┣ server.py           # Dash应用实例初始化
 ┣ app.py              # 应用入口与根路由
 ┗ requirements.txt    # 项目依赖信息
```

### 4.3 `magic-dash-pro`

```bash
magic-dash-pro
 ┣ assets              # 静态资源目录
 ┣ callbacks           # Dash回调函数模块
 ┣ components          # 可复用页面组件模块
 ┣ configs             # 配置参数模块
 ┣ models              # 数据库模型与初始化脚本
 ┣ utils               # 工具函数模块
 ┣ views               # 页面模块
 ┣ magic_dash_pro.db   # SQLite数据库文件，初始化后自动生成
 ┣ server.py           # Dash应用与后端鉴权初始化
 ┣ app.py              # 应用入口与根路由
 ┗ requirements.txt    # 项目依赖信息
```

<a name="template-guide" ></a>

## 5 模板配置与二次开发说明

### 5.1 `simple-tool` 单页面工具模板

#### 5.1.1 配置参数

`simple-tool` 刻意保持极简，不提供额外配置目录。应用标题、布局、回调和业务逻辑都集中在 `app.py` 中，适合快速写一个单页 Dash 工具。

#### 5.1.2 二次开发建议

1. 在 `app.py` 中修改 `app.layout`，组织页面组件。
2. 在同一文件中新增或调整 `@app.callback`。
3. 如果工具逐渐变复杂，可自行拆出 `components/`、`callbacks/`、`utils/` 等目录。
4. 将新增依赖写入 `requirements.txt`，方便部署环境复现。

### 5.2 `magic-dash` 基础多页面模板

#### 5.2.1 配置参数

基础多页面模板的配置集中在 `configs/`：

| 配置文件 | 参数 | 默认值 | 说明 |
| :-- | :-- | :-- | :-- |
| `base_config.py` | `BaseConfig.app_title` | `Magic Dash` | 应用标题，同时影响浏览器标题和页面标题展示 |
| `base_config.py` | `BaseConfig.app_version` | `dev` | 应用版本号，生成项目时会替换为当前 `magic-dash` 版本 |
| `base_config.py` | `BaseConfig.enable_version_changelog_modal` | `False` | 是否启用版本更新日志通知弹窗 |
| `base_config.py` | `BaseConfig.version_changelog_markdown_folder` | `changelogs` | 更新日志 Markdown 文件目录 |
| `base_config.py` | `BaseConfig.min_browser_versions` | Chrome 88 / Firefox 78 / Edge 100 | 浏览器最低版本限制规则 |
| `base_config.py` | `BaseConfig.strict_browser_type_check` | `False` | 是否拦截不在最低版本规则内的浏览器类型 |
| `layout_config.py` | `LayoutConfig.core_side_width` | `350` | 核心页面侧边栏像素宽度 |
| `layout_config.py` | `LayoutConfig.core_layout_type` | `single` | 核心内容区呈现方式，可选 `single`、`tabs` |
| `layout_config.py` | `LayoutConfig.show_core_page_search` | `True` | 是否在页首展示页面搜索框 |
| `router_config.py` | `RouterConfig.index_pathname` | `/index` | 首页路径别名 |
| `router_config.py` | `RouterConfig.core_side_menu` | 内置示例菜单结构 | 侧边菜单结构 |
| `router_config.py` | `RouterConfig.valid_pathnames` | 内置示例页面映射 | 有效路径与页面标题映射 |
| `router_config.py` | `RouterConfig.independent_core_pathnames` | 内置独立页面示例 | 需要跳过核心框架、独立渲染的页面路径 |
| `router_config.py` | `RouterConfig.side_menu_open_keys` | 内置子菜单示例 | 访问指定路径时自动展开的侧边菜单层级 |
| `router_config.py` | `RouterConfig.wildcard_patterns` | 内置通配页面示例 | 正则通配页面规则 |

#### 5.2.2 新增普通页面

1. 在 `views/core_pages/` 下新增页面文件，例如 `report.py`，并提供 `render()` 函数。
2. 在 `components/page_content.py` 中引入页面模块，并将目标 `pathname` 映射到页面 `render()`。
3. 在 `configs/router_config.py` 的 `RouterConfig.valid_pathnames` 中加入路径与标题，例如 `"/core/report": "报表页"`。
4. 在 `RouterConfig.core_side_menu` 中加入对应菜单项，`key` 与 `href` 建议保持一致。
5. 如页面有回调，在 `callbacks/core_pages_c/` 下新增回调模块，并确保被对应 `__init__.py` 导入。

#### 5.2.3 新增独立页面

独立页面适合不需要主框架侧边栏和页首的页面，例如大屏页、打印页、嵌入页。

1. 在 `views/core_pages/` 下新增独立页面模块。
2. 在 `RouterConfig.valid_pathnames` 中声明路径。
3. 在 `RouterConfig.independent_core_pathnames` 中加入该路径。
4. 在 `views/core_pages/__init__.py` 的独立渲染逻辑中返回对应页面。

#### 5.2.4 新增通配页面

通配页面适合详情页、动态参数页等场景。

1. 在 `RouterConfig.wildcard_patterns` 中新增正则规则，例如 `re.compile(r"^/core/order/(.*?)$")`。
2. 将该正则对象加入 `RouterConfig.valid_pathnames`，值为页面标题。
3. 如需独立渲染，将该正则对象加入 `RouterConfig.independent_core_pathnames`。
4. 在渲染函数中接收当前 `pathname`，自行解析动态参数。

### 5.3 `magic-dash-pro` 多页面+用户登录模板

`magic-dash-pro` 在基础多页面模板之上增加登录页、会话管理、角色权限、用户管理、部门管理、登录日志、数据库模型、RSA 登录密码加密等能力。生成该模板时需要选择后端类型：

- `Flask`：默认选项，兼容原有 `magic-dash-pro` 实现，基于 `flask-login` 和 `flask-principal`。
- `FastAPI`：基于 Dash 新版本 `backend="fastapi"`，使用 `fastapi-login` 替换 Flask 登录相关实现。

两个后端版本的 Dash 回调函数都保持同步函数写法，不需要为了 FastAPI 后端把现有回调改成 `async def`。

#### 5.3.1 默认 Flask 后端

生成方式：

```bash
magic-dash create --name magic-dash-pro
```

在“后端类型”提示处直接回车，生成默认 Flask 后端版本。

核心实现：

| 文件 | 说明 |
| :-- | :-- |
| `server.py` | 创建 `dash.Dash()` 应用实例，初始化 `flask-login`、`flask-principal`、浏览器版本拦截 |
| `callbacks/login_c.py` | 登录表单校验、密码解密、会话登录、登录日志记录 |
| `app.py` | 根路由、登录态校验、权限校验、登出逻辑、重复登录检测 |
| `components/personal_info.py` | 当前用户个人信息修改 |
| `views/core_pages/__init__.py` | 登录后核心页面框架与用户菜单 |

#### 5.3.2 FastAPI 后端

生成方式：

```bash
magic-dash create --name magic-dash-pro
```

在后端类型单选菜单中使用方向键选择 `FastAPI` 后回车。

核心实现：

| 文件 | 说明 |
| :-- | :-- |
| `server.py` | 创建 `dash.Dash(..., backend="fastapi")` 应用实例，初始化 `fastapi-login`，提供当前用户与请求代理对象 |
| `callbacks/login_c.py` | 保持同步回调，登录成功后通过 `fastapi-login` 签发 cookie JWT |
| `app.py` | 根路由、登录态校验、权限校验、登出逻辑、重复登录检测 |
| `configs/base_config.py` | 使用不低于 32 字节的默认 `app_secret_key`，避免 JWT HMAC 密钥长度警告 |

FastAPI 后端版本会生成隐藏模板 `magic-dash-pro-fastapi` 的内容，但对用户仍表现为 `magic-dash-pro` 的一个后端选项。页面标题、登录页文案和主界面品牌名称均保持 `Magic Dash Pro`。

#### 5.3.3 Pro 模板公共配置参数

以下参数适用于 Flask 后端和 FastAPI 后端，除特别说明外，两者含义一致：

| 配置文件 | 参数 | 默认值 | 说明 |
| :-- | :-- | :-- | :-- |
| `base_config.py` | `BaseConfig.app_title` | `Magic Dash Pro` | 应用标题 |
| `base_config.py` | `BaseConfig.app_version` | `dev` | 应用版本号，生成项目时会替换为当前 `magic-dash` 版本 |
| `base_config.py` | `BaseConfig.enable_version_changelog_modal` | `False` | 是否启用版本更新日志通知弹窗 |
| `base_config.py` | `BaseConfig.version_changelog_markdown_folder` | `changelogs` | 更新日志 Markdown 文件目录 |
| `base_config.py` | `BaseConfig.app_secret_key` | 后端模板内置默认值 | 应用密钥；FastAPI 后端用于签发 JWT，建议生产环境替换为更强随机密钥 |
| `base_config.py` | `BaseConfig.app_session_cookie_name` | 后端模板内置默认值 | 登录会话 cookie 名称，同域多应用部署时建议改成不同值 |
| `base_config.py` | `BaseConfig.enable_duplicate_login_check` | `False` | 是否开启重复登录检测 |
| `base_config.py` | `BaseConfig.duplicate_login_check_interval` | `10` | 重复登录检测轮询间隔，单位：秒 |
| `base_config.py` | `BaseConfig.session_token_cookie_name` | `session_token` | 重复登录检测使用的会话 token cookie 名称 |
| `base_config.py` | `BaseConfig.enable_fullscreen_watermark` | `False` | 是否启用全屏水印 |
| `base_config.py` | `BaseConfig.fullscreen_watermark_generator` | 当前用户名 | 水印内容生成函数，接收当前用户对象 |
| `base_config.py` | `BaseConfig.rsa_public_key_path` | `magic_dash_pro_public_key.pem` | 登录密码加密传输使用的 RSA 公钥路径 |
| `base_config.py` | `BaseConfig.rsa_private_key_path` | `magic_dash_pro_private_key.pem` | 登录密码加密传输使用的 RSA 私钥路径 |
| `base_config.py` | `BaseConfig.enable_login_captcha` | `False` | 是否启用登录页滑块验证 |
| `base_config.py` | `BaseConfig.min_browser_versions` | Chrome 88 / Firefox 78 / Edge 100 | 浏览器最低版本限制规则 |
| `base_config.py` | `BaseConfig.strict_browser_type_check` | `False` | 是否拦截不在最低版本规则内的浏览器类型 |
| `layout_config.py` | `LayoutConfig.login_left_side_content_type` | `image` | 登录页左侧内容，可选 `image`、`video` |
| `layout_config.py` | `LayoutConfig.core_side_width` | `350` | 核心页面侧边栏像素宽度 |
| `layout_config.py` | `LayoutConfig.core_layout_type` | `single` | 核心内容区呈现方式，可选 `single`、`tabs` |
| `layout_config.py` | `LayoutConfig.show_core_page_search` | `True` | 是否在页首展示页面搜索框 |
| `auth_config.py` | `AuthConfig.roles` | `admin`、`normal` | 系统角色定义 |
| `auth_config.py` | `AuthConfig.normal_role` | `normal` | 常规用户角色键名 |
| `auth_config.py` | `AuthConfig.admin_role` | `admin` | 管理员角色键名 |
| `auth_config.py` | `AuthConfig.pathname_access_rules` | 管理员全部可访问，常规用户排除登录日志页 | 不同角色的页面可访问规则 |
| `database_config.py` | `DatabaseConfig.database_type` | `sqlite` | 数据库类型，可选 `sqlite`、`postgresql`、`mysql` |
| `database_config.py` | `DatabaseConfig.postgresql_config` | 本地示例配置 | PostgreSQL 连接配置 |
| `database_config.py` | `DatabaseConfig.mysql_config` | 本地示例配置 | MySQL 连接配置 |

FastAPI 后端额外包含：

| 配置文件 | 参数 | 默认值 | 说明 |
| :-- | :-- | :-- | :-- |
| `base_config.py` | `BaseConfig.login_session_expire_seconds` | `12 * 60 * 60` | 未勾选“记住我”时的登录有效期，单位：秒 |
| `base_config.py` | `BaseConfig.remember_login_expire_seconds` | `30 * 24 * 60 * 60` | 勾选“记住我”后的登录有效期，单位：秒 |

#### 5.3.4 用户、角色与权限二次开发

新增角色：

1. 在 `configs/auth_config.py` 的 `AuthConfig.roles` 中加入角色定义。
2. 在 `AuthConfig.pathname_access_rules` 中为新角色配置页面访问规则。
3. 在用户管理页面中为用户分配对应角色，或在初始化脚本中创建带新角色的用户。

权限规则说明：

```python
{
    "admin": {"type": "all"},
    "normal": {
        "type": "exclude",
        "keys": ["/core/login-logs"],
    },
}
```

- `all`：可访问全部有效页面。
- `include`：仅可访问 `keys` 中列出的页面，首页会自动纳入。
- `exclude`：不可访问 `keys` 中列出的页面。

新增受权限控制的业务页面时，应同步维护 `RouterConfig.valid_pathnames`、`RouterConfig.core_side_menu` 和 `AuthConfig.pathname_access_rules`。

#### 5.3.5 数据库二次开发

默认使用 SQLite，适合本地开发和轻量部署。切换到 PostgreSQL 或 MySQL：

1. 修改 `configs/database_config.py` 中的 `DatabaseConfig.database_type`。
2. 填写 `postgresql_config` 或 `mysql_config`。
3. 安装对应数据库驱动。
4. 重新执行 `python -m models.init_db` 初始化表结构和初始管理员数据。

新增业务表：

1. 在 `models/` 下新增模型文件，继承 `BaseModel`。
2. 在模型中封装常用查询、创建、更新、删除方法。
3. 将新模型加入初始化流程，确保部署时可以创建表。
4. 页面回调中通过模型方法读写数据，避免在回调里散落 SQL 或底层 ORM 细节。

#### 5.3.6 登录页和安全相关二次开发

- 登录页结构在 `views/login.py`，登录逻辑在 `callbacks/login_c.py`。
- 登录密码默认通过浏览器 Web Crypto API 使用 RSA 公钥加密后传到后端，再由后端私钥解密。
- RSA 密钥文件由 `python -m models.init_db` 初始化生成。
- 生产环境建议替换 `BaseConfig.app_secret_key`，并妥善管理 RSA 私钥文件。
- 同一域名或同一主机多应用部署时，建议修改 `app_session_cookie_name` 和 `session_token_cookie_name`，避免 cookie 串扰。

#### 5.3.7 Pro 模板新增页面

Pro 模板新增页面的步骤与 `magic-dash` 基础模板一致，但要额外考虑权限：

1. 新增 `views/core_pages/xxx.py` 页面模块。
2. 在 `components/page_content.py` 中接入页面渲染。
3. 在 `configs/router_config.py` 中维护菜单和有效路径。
4. 在 `configs/auth_config.py` 中维护角色访问规则。
5. 如有回调，在 `callbacks/core_pages_c/` 中新增模块并导入。

#### 5.3.8 Pro 模板部署提示

- 本地开发可直接运行 `python app.py`。
- Flask 后端生产部署可按实际项目习惯接入 WSGI 服务。
- FastAPI 后端底层为 ASGI 应用，`python app.py` 会通过 Dash 的 FastAPI 后端启动逻辑运行；生产环境可结合 ASGI 服务部署生成项目中的 `server`。
- 部署前建议固定依赖版本、替换密钥、确认数据库配置、关闭调试模式，并按实际反向代理环境配置 cookie、安全头和静态资源策略。

<a name="changelog" ></a>

## 6 更新日志

[历史版本更新日志](./changelog.md)

<a name="courses" ></a>

## 7 更多应用开发教程

> 微信公众号「玩转 Dash」，欢迎扫码关注 👇

<p align="center" >
  <img src="./imgs/公众号.png" height=220 />
</p>

> 「玩转 Dash」知识星球，海量教程案例模板资源，专业的答疑咨询服务，欢迎扫码加入 👇

<p align="center" >
  <img src="./imgs/知识星球.jpg" height=220 />
</p>
