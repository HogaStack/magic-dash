# `magic-dash-pro` FastAPI 后端模板

`magic-dash-pro` 的 `FastAPI` 后端对应隐藏模板 `magic_dash/templates/magic-dash-pro-fastapi`。它仍以 `magic-dash-pro` 的方式对用户暴露，但底层使用 [`Dash`](https://github.com/plotly/dash) 的 `backend="fastapi"` 能力，结合 [`FastAPI`](https://github.com/fastapi/fastapi) 与 [`fastapi-login`](https://github.com/MushroomMaula/fastapi_login) 实现登录态。

## 创建方式

```bash
magic-dash create --name magic-dash-pro
```

在后端选择菜单中选择 `FastAPI`。

不能直接执行：

```bash
magic-dash create --name magic-dash-pro-fastapi
```

## 依赖

核心依赖包括：

```text
dash[fastapi]>=4.2.0rc3,<5.0.0
fastapi-login
peewee
cryptography
user_agents
Werkzeug
```

组件相关依赖与 `Flask` 后端保持一致：

- [`feffery-antd-components`](https://github.com/CNFeffery/feffery-antd-components)
- [`feffery-utils-components`](https://github.com/CNFeffery/feffery-utils-components)
- [`feffery-dash-utils`](https://github.com/CNFeffery/feffery-dash-utils)
- [`feffery-markdown-components`](https://github.com/CNFeffery/feffery-markdown-components)

## 服务初始化

`server.py` 使用 `backend="fastapi"` 创建 `Dash` 应用：

```python
app = dash.Dash(
    __name__,
    title=BaseConfig.app_title,
    suppress_callback_exceptions=True,
    compress=True,
    update_title=None,
    backend="fastapi",
)

server = app.server
```

这里的 `server` 是 `FastAPI` 应用对象，适合接入 `ASGI` 部署链路。

## 登录态设计

模板使用 `fastapi-login` 的 `LoginManager`：

- `BaseConfig.app_secret_key` 用于签发登录 `JWT`。
- `BaseConfig.app_session_cookie_name` 用于保存登录 `cookie`。
- `BaseConfig.login_session_expire_seconds` 控制普通登录有效期。
- `BaseConfig.remember_login_expire_seconds` 控制勾选“记住我”后的有效期。

登录成功后，模板通过 `dash.ctx.response.set_cookie()` 写入登录 `cookie`。

## 同步回调兼容层

`Dash` 回调仍保持同步函数写法，不需要改成 `async def`。为了兼容原有 `Flask` 后端中常用的 `current_user` 和 `request` 访问方式，模板提供了两个轻量代理：

- `CurrentUserProxy`：面向当前请求读取用户对象。
- `RequestProxy`：提供类似 `Flask request` 的 `cookies`、`remote_addr`、`user_agent`、`path` 属性。

这样大部分页面回调和业务逻辑可以保持与 `Flask` 后端相近的写法。

## 中间件

`server.py` 注册了 `FastAPI` 中间件 `load_auth_and_check_browser`，在每个请求进入后执行：

1. 检查浏览器版本，拦截低版本浏览器或 `Internet Explorer`。
2. 对静态资源和 `Dash` 内部请求跳过鉴权加载。
3. 使用 `manager.optional(request)` 尝试加载当前用户。
4. 将当前用户写入 `request.state.current_user`。

未登录用户会被表示为 `AnonymousUser`。

## 登录流程

核心文件：

| 文件 | 职责 |
| --- | --- |
| `views/login.py` | 登录页布局 |
| `callbacks/login_c.py` | 登录表单校验、密码解密、用户匹配、签发登录 `cookie` |
| `server.py` | `LoginManager`、当前用户代理、请求代理、中间件 |
| `app.py` | 页面登录态检查、权限检查、退出逻辑、重复登录检测 |
| `models/users.py` | 用户查询与管理 |
| `models/logs.py` | 登录日志写入与查询 |

## 数据库初始化

启动前执行：

```bash
python -m models.init_db
```

该命令与 `Flask` 后端版本保持一致，会创建表、初始化管理员账号并生成 `RSA` 密钥。

## 配置差异

`FastAPI` 后端额外包含：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `BaseConfig.login_session_expire_seconds` | `12 * 60 * 60` | 未勾选“记住我”时的登录有效期 |
| `BaseConfig.remember_login_expire_seconds` | `30 * 24 * 60 * 60` | 勾选“记住我”后的登录有效期 |

`BaseConfig.app_secret_key` 在 `FastAPI` 后端中用于 `JWT HMAC` 签名，生产环境应替换为足够强的随机密钥。

## 部署提示

本地开发：

```bash
python app.py
```

生产环境可按 `ASGI` 应用方式部署 `server`。部署前建议：

- 替换 `BaseConfig.app_secret_key`。
- 固定 `dash[fastapi]` 和 `fastapi-login` 版本。
- 检查 `cookie` 域名、路径、`SameSite` 和反向代理配置。
- 妥善管理 `RSA` 私钥。
- 确认数据库连接配置。

## 与 Flask 后端的差异

| 对比项 | FastAPI 后端 |
| --- | --- |
| 底层服务 | `Dash` 的 `backend="fastapi"` |
| 登录态 | `fastapi-login` 签发的 `cookie JWT` |
| 当前用户 | `request.state.current_user` 加代理对象 |
| 请求对象 | `RequestProxy` 兼容层 |
| 部署形态 | `ASGI` |

如果需要默认 `Dash` 和 `Flask` 生态方式，请查看 [`magic-dash-pro` Flask 后端模板](./magic-dash-pro-flask.md)。
