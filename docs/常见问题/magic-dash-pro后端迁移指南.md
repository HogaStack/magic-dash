# `magic-dash-pro`后端迁移指南

本文介绍如何将原本基于`Flask`后端创建的`magic-dash-pro`项目迁移到`FastAPI`后端。适用场景包括：项目需要更强的并发服务能力、原生异步接口、`WebSocket`、更清晰的接口类型标注，或希望将已有[Dash](https://github.com/plotly/dash)应用逐步接入`FastAPI`生态。

## 推荐迁移方式

推荐使用“新建`FastAPI`后端项目，再迁移业务代码”的方式，而不是在原项目中直接逐文件硬改：

```bash
magic-dash create --name magic-dash-pro --backend fastapi
```

等价的简写形式为`magic-dash create -n magic-dash-pro -b fastapi`。

生成一个新的`FastAPI`后端目标项目。随后将原`Flask`后端项目中的业务内容迁移到新项目中。

优先迁移这些目录：

- `views/`：页面渲染模块
- `callbacks/`：业务回调
- `components/`：自定义功能组件
- `models/`：自定义数据模型
- `assets/`：静态资源
- `configs/`：按需迁移业务配置项

不建议直接覆盖这些文件：

- `server.py`
- `app.py`
- `callbacks/login_c.py`
- 与登录、登出、鉴权强相关的模板文件

这些文件在`Flask`和`FastAPI`后端中实现方式不同，应以新`FastAPI`模板为基准，再合并原项目中的业务改动。

如果项目启用了邮件验证码登录，还应以新模板中的`configs/email_config.py`、`models/email_verifications.py`和`utils/email_utils.py`为基准。两种后端的邮件配置和验证码模型一致，但登录会话的建立仍由各自的`callbacks/login_c.py`完成，因此不应直接用`Flask`版本覆盖`FastAPI`版本。

## 依赖调整

`Flask`后端常见依赖：

```text
dash>=4.2.0,<5.0.0
Flask_Login
flask-principal
flask-compress
```

迁移到`FastAPI`后端后，应以新模板的`requirements.txt`为准，核心差异是：

```text
dash[fastapi]>=4.2.0,<5.0.0
fastapi-login
Werkzeug
```

说明：

- `Flask_Login`替换为`fastapi-login`。
- `flask-principal`不再作为权限系统入口，页面权限仍建议由`AuthConfig.pathname_access_rules`和模板中的路由校验逻辑控制。
- `Werkzeug`仍会用于密码哈希校验等能力。
- 如项目使用`PostgreSQL`或`MySQL`，仍需保留对应数据库驱动依赖。

## 核心文件迁移

### `server.py`

`FastAPI`后端模板中的`server.py`已经完成以下工作：

- 使用`dash.Dash(..., backend="fastapi")`创建应用。
- 通过`fastapi-login`管理登录`cookie`。
- 提供`current_user`代理对象，兼容同步[Dash](https://github.com/plotly/dash)回调中的当前用户访问。
- 提供`request`代理对象，兼容常见的`request.cookies`、`request.remote_addr`、`request.user_agent`、`request.path`访问。
- 使用`@app.server.middleware("http")`加载当前用户并执行浏览器版本检查。

因此迁移时建议直接采用新`FastAPI`模板的`server.py`，再把原项目中确实需要保留的自定义接口、中间件或工具函数迁移进去。

### `app.py`

`Flask`后端中常见导入方式：

```python
from flask import request
from flask_login import current_user, logout_user, AnonymousUserMixin
from flask_principal import identity_changed, AnonymousIdentity

from server import app
```

迁移到`FastAPI`后端后，推荐改为：

```python
from server import app, current_user, logout_current_user, request
```

对应调整：

- `logout_user()`改为`logout_current_user()`。
- `AnonymousUserMixin`判断改为`if not current_user.is_authenticated`。
- `identity_changed.send(...)`和`AnonymousIdentity()`相关逻辑通常可以删除。
- `request.cookies.get(...)`可继续使用模板提供的`request`代理。

### `callbacks/login_c.py`

`Flask`后端登录逻辑通常包含：

```python
from flask_login import login_user
from flask_principal import identity_changed, Identity
```

迁移到`FastAPI`后端后，改为：

```python
from server import app, User, login_current_user, request
```

登录状态写入逻辑从：

```python
login_user(new_user, remember=remember_me)
identity_changed.send(app.server, identity=Identity(new_user.id))
```

改为：

```python
login_current_user(new_user, remember=remember_me)
```

如果原项目中对登录成功后写入`cookie`、记录登录日志、更新`session_token`有自定义逻辑，可以保留，但应确认最终通过`dash.ctx.response.set_cookie(...)`或`login_current_user(...)`写入响应。

## `Flask`原生能力迁移示例

### 原生接口路由

`Flask`写法：

```python
@app.server.route("/api/health", methods=["GET"])
def health():
    return {"status": "ok"}
```

`FastAPI`写法：

```python
@app.server.get("/api/health")
async def health():
    return {"status": "ok"}
```

带参数的接口：

```python
from fastapi import Query


@app.server.get("/api/users")
async def list_users(keyword: str = Query(default="")):
    return {"keyword": keyword}
```

### 请求对象

`Flask`写法：

```python
from flask import request


@app.server.route("/api/search", methods=["POST"])
def search():
    payload = request.get_json()
    keyword = request.args.get("keyword")
    token = request.cookies.get("token")
    return {"keyword": keyword, "payload": payload, "token": token}
```

`FastAPI`写法：

```python
from fastapi import Request


@app.server.post("/api/search")
async def search(request: Request):
    payload = await request.json()
    keyword = request.query_params.get("keyword")
    token = request.cookies.get("token")
    return {"keyword": keyword, "payload": payload, "token": token}
```

常见替换关系：

| `Flask` | `FastAPI` |
| --- | --- |
| `request.args.get("key")` | `request.query_params.get("key")` |
| `request.get_json()` | `await request.json()` |
| `request.form` | `await request.form()` |
| `request.headers.get("x")` | `request.headers.get("x")` |
| `request.cookies.get("x")` | `request.cookies.get("x")` |
| `request.remote_addr` | `request.client.host` |

### 返回响应

`Flask`写法：

```python
from flask import jsonify, abort


@app.server.route("/api/item/<item_id>")
def get_item(item_id):
    if item_id == "0":
        abort(404)
    return jsonify({"item_id": item_id})
```

`FastAPI`写法：

```python
from fastapi import HTTPException


@app.server.get("/api/item/{item_id}")
async def get_item(item_id: str):
    if item_id == "0":
        raise HTTPException(status_code=404, detail="item not found")
    return {"item_id": item_id}
```

文件响应可使用：

```python
from fastapi.responses import FileResponse


@app.server.get("/download/report")
async def download_report():
    return FileResponse("reports/demo.xlsx", filename="demo.xlsx")
```

### `before_request`与中间件

`Flask`写法：

```python
@app.server.before_request
def load_trace_id():
    request.trace_id = request.headers.get("x-trace-id")
```

`FastAPI`写法：

```python
@app.server.middleware("http")
async def load_trace_id(request, call_next):
    request.state.trace_id = request.headers.get("x-trace-id")
    response = await call_next(request)
    return response
```

在接口中读取：

```python
from fastapi import Request


@app.server.get("/api/trace")
async def trace(request: Request):
    return {"trace_id": request.state.trace_id}
```

如果只是[Dash](https://github.com/plotly/dash)回调中读取当前请求的轻量信息，优先使用`server.py`中已有的`request`代理；如果是`FastAPI`原生接口或中间件，请使用`fastapi.Request`。

### `g`、`session`与上下文变量

`Flask`中常见写法：

```python
from flask import g, session

g.trace_id = "..."
session["active_tab"] = "overview"
```

迁移建议：

- 单次请求内临时变量：改为`request.state`。
- 跨请求状态：优先放入数据库、缓存或前端`dcc.Store`。
- 登录状态：使用模板内置的`fastapi-login`和`login_current_user()`。
- 不建议把大量业务状态继续塞进服务端`session`，这会增加迁移和部署复杂度。

示例：

```python
@app.server.middleware("http")
async def bind_context(request, call_next):
    request.state.trace_id = request.headers.get("x-trace-id")
    return await call_next(request)
```

### `Blueprint`迁移为`APIRouter`

`Flask Blueprint`写法：

```python
from flask import Blueprint

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/reports")
def reports():
    return {"items": []}


app.server.register_blueprint(api)
```

`FastAPI APIRouter`写法：

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/reports")
async def reports():
    return {"items": []}


app.server.include_router(router)
```

### `WebSocket`

如果迁移目标是使用`WebSocket`，应使用`FastAPI`原生能力：

```python
from fastapi import WebSocket


@app.server.websocket("/ws/progress")
async def progress(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"status": "connected"})
    await websocket.close()
```

[Dash](https://github.com/plotly/dash)页面中可以通过前端组件或自定义客户端脚本连接该`WebSocket`地址。

## 权限逻辑迁移

`Flask`后端模板中使用`flask-principal`辅助角色权限识别；`FastAPI`后端模板不再依赖`flask-principal`，而是在请求中间件里加载当前用户，再由应用路由逻辑根据`AuthConfig.pathname_access_rules`判断页面访问权限。

如果原项目中有类似写法：

```python
from server import user_permissions


@user_permissions["admin"].require()
def admin_only_task():
    ...
```

迁移后建议改为显式判断当前用户角色：

```python
from fastapi import HTTPException, Request
from configs import AuthConfig


def require_admin(request: Request):
    current_user = getattr(request.state, "current_user", None)
    if not current_user or current_user.user_role != AuthConfig.admin_role:
        raise HTTPException(status_code=403, detail="permission denied")
    return current_user
```

用于接口：

```python
from fastapi import Depends


@app.server.get("/api/admin/users")
async def admin_users(current_user=Depends(require_admin)):
    return {"role": current_user.user_role}
```

[Dash](https://github.com/plotly/dash)页面权限仍推荐通过`configs/auth_config.py`和`configs/router_config.py`统一管理。

## 部署命令

迁移到`FastAPI`后端后，推荐使用`uvicorn`直接启动`app.py`中`Dash`实例内置的`FastAPI`服务对象。参考部署命令：

```bash
uvicorn app:app.server --host 0.0.0.0 --port 8050 --workers 4
```

说明：

- 第一个`app`是`app.py`模块名。
- 第二个`app`是`app.py`中导入的[Dash](https://github.com/plotly/dash)实例。
- `app.server`即该[Dash](https://github.com/plotly/dash)实例内置的`FastAPI`实例。
- 迁移后不再推荐把`python app.py`作为生产部署命令。

## 迁移检查清单

- 已使用新`FastAPI`模板的`server.py`作为基准。
- 已将`requirements.txt`切换为`dash[fastapi]`和`fastapi-login`相关依赖。
- 已将`flask_login.current_user`替换为`server.current_user`。
- 已将`flask_login.login_user`替换为`login_current_user()`。
- 已将`flask_login.logout_user`替换为`logout_current_user()`。
- 已移除`flask_principal`相关身份切换逻辑。
- 原`Flask`接口已改写为`FastAPI`路由。
- 原`before_request`逻辑已改写为`FastAPI`中间件。
- 原`g`、`session`上下文依赖已迁移到`request.state`、数据库、缓存或前端状态。
- 如启用邮件验证码登录，已迁移`EmailConfig`中的`SMTP`配置，并确认用户邮箱保持唯一。
- 已在目标项目运行`python -m magic_init`，创建或升级用户邮箱和邮件验证码相关表结构。
- 部署命令已切换为`uvicorn app:app.server --host 0.0.0.0 --port 8050 --workers 4`。
