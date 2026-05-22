# `magic-dash-pro` Flask 后端模板

`magic-dash-pro` 的 `Flask` 后端是默认后端模板，对应源码目录 `magic_dash/templates/magic-dash-pro`。它基于 [`Dash`](https://github.com/plotly/dash) 默认的 [`Flask`](https://github.com/pallets/flask) 服务能力，并使用 [`flask-login`](https://github.com/maxcountryman/flask-login) 管理登录会话，使用 [`flask-principal`](https://github.com/mattupstate/flask-principal) 承载角色权限。

## 创建方式

```bash
magic-dash create --name magic-dash-pro
```

在后端选择菜单中直接回车即可使用默认 `Flask` 后端。

## 依赖

核心依赖包括：

```text
dash>=3.4.0,<4.0.0
flask-login
flask-principal
peewee
cryptography
user_agents
flask-compress
```

组件相关依赖：

- [`feffery-antd-components`](https://github.com/CNFeffery/feffery-antd-components)
- [`feffery-utils-components`](https://github.com/CNFeffery/feffery-utils-components)
- [`feffery-dash-utils`](https://github.com/CNFeffery/feffery-dash-utils)
- [`feffery-markdown-components`](https://github.com/CNFeffery/feffery-markdown-components)

## 服务初始化

`server.py` 负责创建应用实例：

```python
app = dash.Dash(
    __name__,
    title=BaseConfig.app_title,
    suppress_callback_exceptions=True,
    compress=True,
    update_title=None,
)

server = app.server
```

随后配置：

- `SECRET_KEY`：来自 `BaseConfig.app_secret_key`。
- `SESSION_COOKIE_NAME`：来自 `BaseConfig.app_session_cookie_name`。
- `LoginManager`：用于加载和维护当前用户。
- `Principal`：用于角色权限体系。
- `before_request`：用于浏览器最低版本检查。

## 登录态加载

`flask-login` 的 `user_loader` 会根据会话中的用户 `id` 查询 `Users` 模型。模板为了减少静态资源请求带来的数据库开销，会跳过以下请求：

- `/_reload-hash`
- `/_dash-layout`
- `/_dash-dependencies`
- `/assets/`
- `/_dash-component-suites/`

匹配到有效用户后，会构造内部 `User` 对象，包含：

- `id`
- `user_name`
- `user_role`
- `session_token`

## 权限加载

`flask-principal` 通过 `identity_loaded` 信号把当前用户角色写入 `identity.provides`，之后业务逻辑可以基于角色判断页面访问权限。

模板中页面级权限主要由 `configs/auth_config.py` 的 `AuthConfig.pathname_access_rules` 驱动。

## 登录流程

核心文件：

| 文件 | 职责 |
| --- | --- |
| `views/login.py` | 登录页布局 |
| `callbacks/login_c.py` | 登录表单校验、密码解密、用户匹配、登录日志写入 |
| `app.py` | 登录态检查、页面权限检查、登出逻辑、重复登录检测 |
| `models/users.py` | 用户查询与管理 |
| `models/logs.py` | 登录日志写入与查询 |

流程概览：

1. 用户访问受保护页面。
2. `app.py` 判断未登录后渲染登录页。
3. 前端使用 `RSA` 公钥加密密码。
4. `callbacks/login_c.py` 解密密码并校验用户。
5. 校验通过后调用 `flask-login` 写入登录态。
6. 记录登录日志。
7. 跳转到核心页面。

## 数据库初始化

启动前执行：

```bash
python -m models.init_db
```

该命令会：

- 创建用户表和部门表。
- 初始化管理员账号 `admin/admin123`。
- 生成 `RSA` 公私钥。
- 在已有数据时询问是否重置。

## 部署提示

本地开发可以直接运行：

```bash
python app.py
```

生产环境中，`server.py` 暴露了 `server = app.server`，可按常规 `WSGI` 方式接入部署链路。部署前建议：

- 替换 `BaseConfig.app_secret_key`。
- 修改 `app_session_cookie_name`，避免同域多应用冲突。
- 妥善管理 `RSA` 私钥。
- 根据目标数据库调整 `DatabaseConfig`。
- 关闭调试模式。

## 与 FastAPI 后端的差异

| 对比项 | Flask 后端 |
| --- | --- |
| 底层服务 | `Dash` 默认 `Flask` 服务 |
| 登录态 | `flask-login` 会话 |
| 权限基础 | `flask-principal` |
| 部署形态 | `WSGI` |
| 当前用户对象 | 直接使用 `flask_login.current_user` |

如果需要 `ASGI` 服务形态，请查看 [`magic-dash-pro` FastAPI 后端模板](./magic-dash-pro-fastapi.md)。
