# `magic-dash-pro` 模板介绍

`magic-dash-pro` 是 `magic-dash` 中能力最完整的管理系统模板。它在 [`magic-dash`](./magic-dash.md) 基础多页面结构之上增加登录鉴权、角色权限、用户管理、部门管理、登录日志、数据库模型、登录密码加密传输等后台系统常用能力。

## 适用场景

优先选择 `magic-dash-pro` 的典型情况：

- 需要用户登录和退出。
- 需要基于角色控制页面访问权限。
- 需要内置用户管理、部门管理、登录日志。
- 需要用数据库保存用户、部门、日志或业务数据。
- 需要一个可继续扩展为内部管理系统的 `Dash` 项目骨架。
- 需要在 [`Flask`](https://github.com/pallets/flask) 与 [`FastAPI`](https://github.com/fastapi/fastapi) 后端之间选择。

## 创建方式

```bash
magic-dash create --name magic-dash-pro
```

执行后会继续选择后端类型：

- `Flask`：默认选项。
- `FastAPI`：使用方向键选择后回车。

也可以通过环境变量在自动化场景中指定后端：

```bash
MAGIC_DASH_PRO_BACKEND=flask magic-dash create --name magic-dash-pro
MAGIC_DASH_PRO_BACKEND=fastapi magic-dash create --name magic-dash-pro
```

在 `PowerShell` 中可写作：

```powershell
$env:MAGIC_DASH_PRO_BACKEND = "fastapi"
magic-dash create --name magic-dash-pro
```

## 启动方式

```bash
cd magic-dash-pro
pip install -r requirements.txt
python -m models.init_db
python app.py
```

默认访问地址：

```text
http://127.0.0.1:8050
```

默认管理员账号：

```text
用户名：admin
密码：admin123
```

## 后端模板

`magic-dash-pro` 是面向用户的顶层模板名。生成时根据后端选择复制不同底层模板：

| 后端选择 | 实际底层模板 | 说明 | 专项文档 |
| --- | --- | --- | --- |
| `Flask` | `magic-dash-pro` | 默认后端，基于 [`flask-login`](https://github.com/maxcountryman/flask-login) 和 [`flask-principal`](https://github.com/mattupstate/flask-principal) | [查看](./magic-dash-pro-flask.md) |
| `FastAPI` | `magic-dash-pro-fastapi` | 隐藏模板，基于 `Dash` 的 `backend="fastapi"` 和 [`fastapi-login`](https://github.com/MushroomMaula/fastapi_login) | [查看](./magic-dash-pro-fastapi.md) |

`magic-dash-pro-fastapi` 不会出现在 `magic-dash list` 中，也不能通过 `magic-dash create --name magic-dash-pro-fastapi` 直接创建。

## 通用目录结构

两个后端版本都保持相同的高层目录约定：

```text
magic-dash-pro/
├─ assets/
│  ├─ css/
│  ├─ imgs/
│  ├─ js/
│  ├─ videos/
│  └─ favicon.ico
├─ callbacks/
│  ├─ login_c.py
│  └─ core_pages_c/
├─ components/
├─ configs/
│  ├─ auth_config.py
│  ├─ base_config.py
│  ├─ database_config.py
│  ├─ layout_config.py
│  └─ router_config.py
├─ models/
├─ utils/
├─ views/
│  ├─ login.py
│  ├─ core_pages/
│  └─ status_pages/
├─ server.py
├─ app.py
└─ requirements.txt
```

## 通用功能

### 登录鉴权

模板提供登录页、登录回调、退出逻辑和登录态校验。登录成功后进入核心页面框架，未登录访问受保护页面时会被引导到登录页。

### 角色权限

`configs/auth_config.py` 中定义角色和页面访问规则。默认角色：

- `admin`：系统管理员。
- `normal`：常规用户。

访问规则支持：

- `all`：允许访问全部有效页面。
- `include`：仅允许访问指定页面。
- `exclude`：禁止访问指定页面。

### 数据库模型

默认使用 [`peewee`](https://github.com/coleifer/peewee) 组织模型层。内置模型包括：

- `Users`：用户信息。
- `Departments`：部门信息。
- `Logs`：登录日志。

默认数据库为 `SQLite`，也可以通过 `DatabaseConfig` 切换到 `PostgreSQL` 或 `MySQL`。

### 数据库初始化

`python -m models.init_db` 会完成以下工作：

- 创建必要数据表。
- 初始化管理员账号。
- 生成登录密码加密传输需要的 `RSA` 公钥和私钥。
- 在已有数据时通过交互提示确认是否重置。

### 登录密码加密传输

模板使用浏览器端 `Web Crypto API` 结合后端 `RSA` 私钥解密流程，降低明文密码在请求体中直接传输的风险。相关密钥路径由 `BaseConfig.rsa_public_key_path` 和 `BaseConfig.rsa_private_key_path` 控制。

### 登录日志

模板内置登录日志页面，对应：

- `models/logs.py`
- `views/core_pages/login_logs.py`
- `callbacks/core_pages_c/login_logs_c.py`

### 用户与部门管理

系统管理相关页面和组件集中在：

- `components/user_manage.py`
- `components/department_manage.py`
- `components/personal_info.py`

### 安全与体验配置

`BaseConfig` 还提供：

- 应用密钥和会话 `cookie` 名称。
- 重复登录检测。
- 全屏水印。
- 登录页滑块验证开关。
- 浏览器最低版本限制。
- 版本更新日志弹窗。

## 后端选择建议

| 选择 | 推荐情况 |
| --- | --- |
| `Flask` | 需要兼容传统 `Dash` 部署方式、已有 [`Flask`](https://github.com/pallets/flask) 生态经验、希望使用 [`flask-login`](https://github.com/maxcountryman/flask-login) 的会话模式 |
| `FastAPI` | 希望使用 `ASGI` 后端、希望与 [`FastAPI`](https://github.com/fastapi/fastapi) 服务集成、希望使用 `cookie JWT` 风格的登录态 |

两个后端版本的页面、配置和大部分回调组织方式保持一致。`FastAPI` 版本为了兼容现有同步 `Dash` 回调，提供了当前用户和请求对象的轻量代理。

## 生产环境注意事项

上线前建议至少检查以下项目：

- 替换 `BaseConfig.app_secret_key`。
- 妥善保存 `RSA` 私钥文件。
- 修改同域多应用部署时可能冲突的 `app_session_cookie_name` 和 `session_token_cookie_name`。
- 确认数据库类型和连接信息。
- 固定依赖版本。
- 关闭调试模式。
- 根据反向代理和域名策略配置 `cookie`、安全头和静态资源缓存。

## 进一步阅读

- [`magic-dash-pro` Flask 后端模板](./magic-dash-pro-flask.md)
- [`magic-dash-pro` FastAPI 后端模板](./magic-dash-pro-fastapi.md)
- [配置参数说明](./configuration.md)
- [二次开发介绍](./development.md)
