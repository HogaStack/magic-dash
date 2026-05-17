from datetime import timedelta

import dash
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi_login import LoginManager
from user_agents import parse

from dash.backends._fastapi import get_current_request
from models.users import Users
from configs import BaseConfig

app = dash.Dash(
    __name__,
    title=BaseConfig.app_title,
    suppress_callback_exceptions=True,
    compress=True,
    update_title=None,
    backend="fastapi",
)
server = app.server


class AnonymousUser:
    """兼容当前模板鉴权逻辑的匿名用户对象"""

    id = None
    user_name = None
    user_role = None
    session_token = None
    is_authenticated = False


class User:
    """fastapi-login专用用户对象"""

    is_authenticated = True

    def __init__(
        self, id: str, user_name: str, user_role: str, session_token: str = None
    ) -> None:
        self.id = id
        self.user_name = user_name
        self.user_role = user_role
        self.session_token = session_token


class CurrentUserProxy:
    """面向同步Dash回调的请求级当前用户代理对象"""

    def _get_current_object(self):
        try:
            request = get_current_request()
        except RuntimeError:
            return AnonymousUser()

        return getattr(request.state, "current_user", AnonymousUser())

    def __getattr__(self, name):
        return getattr(self._get_current_object(), name)

    def __bool__(self):
        return bool(self._get_current_object().is_authenticated)


class RequestProxy:
    """面向现有同步回调的轻量级类Flask请求代理对象"""

    def _get_current_object(self):
        return get_current_request()

    @property
    def cookies(self):
        return self._get_current_object().cookies

    @property
    def remote_addr(self):
        client = self._get_current_object().client
        return getattr(client, "host", None)

    @property
    def user_agent(self):
        return self._get_current_object().headers.get("user-agent", "")

    @property
    def path(self):
        return self._get_current_object().url.path


current_user = CurrentUserProxy()
request = RequestProxy()

manager = LoginManager(
    BaseConfig.app_secret_key,
    token_url="/login",
    use_cookie=True,
    use_header=False,
    cookie_name=BaseConfig.app_session_cookie_name,
    default_expiry=timedelta(seconds=BaseConfig.login_session_expire_seconds),
)


@manager.user_loader()
def user_loader(user_id):
    """fastapi-login内部专用用户加载函数"""

    match_user = Users.get_user(user_id)

    if not match_user:
        return None

    return User(
        id=match_user.user_id,
        user_name=match_user.user_name,
        user_role=match_user.user_role,
        session_token=match_user.session_token,
    )


def _set_current_user(user):
    try:
        get_current_request().state.current_user = user
    except RuntimeError:
        pass


def login_current_user(user, remember: bool = False):
    """基于fastapi-login cookie持久化当前用户登录状态"""

    expires_delta = timedelta(
        seconds=(
            BaseConfig.remember_login_expire_seconds
            if remember
            else BaseConfig.login_session_expire_seconds
        )
    )
    access_token = manager.create_access_token(
        data={"sub": user.id},
        expires=expires_delta,
    )
    cookie_options = {
        "httponly": True,
        "samesite": "lax",
        "path": "/",
    }

    if remember:
        cookie_options["max_age"] = int(expires_delta.total_seconds())

    dash.ctx.response.set_cookie(
        manager.cookie_name,
        access_token,
        **cookie_options,
    )
    _set_current_user(user)


def logout_current_user():
    """清除鉴权相关cookie并重置当前用户状态"""

    dash.ctx.response.set_cookie(
        manager.cookie_name,
        "",
        max_age=0,
        expires=0,
        httponly=True,
        samesite="lax",
        path="/",
    )
    dash.ctx.response.set_cookie(
        BaseConfig.session_token_cookie_name,
        "",
        max_age=0,
        expires=0,
        path="/",
    )
    _set_current_user(AnonymousUser())


def _should_skip_auth(pathname: str):
    return any(
        [
            pathname in ["/_reload-hash", "/_dash-layout", "/_dash-dependencies"],
            pathname.startswith("/assets/"),
            pathname.startswith("/_dash-component-suites/"),
        ]
    )


def _browser_block_message(request: Request):
    user_agent = parse(request.headers.get("user-agent", ""))

    if user_agent.browser.version == ():
        return None

    if user_agent.browser.family == "IE":
        return (
            "<div style='font-size: 16px; color: red; position: fixed; top: 40%; "
            "left: 50%; transform: translateX(-50%);'>"
            "请不要使用Internet Explorer或IE兼容模式访问本应用</div>"
        )

    for rule in BaseConfig.min_browser_versions:
        if (
            user_agent.browser.family == rule["browser"]
            and user_agent.browser.version[0] < rule["version"]
        ):
            return (
                "<div style='font-size: 16px; color: red; position: fixed; top: 40%; "
                "left: 50%; transform: translateX(-50%);'>"
                "您的{}浏览器版本低于本应用最低支持版本（{}），"
                "请升级浏览器后再访问</div>"
            ).format(rule["browser"], rule["version"])

    if BaseConfig.strict_browser_type_check and user_agent.browser.family not in [
        rule["browser"] for rule in BaseConfig.min_browser_versions
    ]:
        return (
            "<div style='font-size: 16px; color: red; position: fixed; top: 40%; "
            "left: 50%; transform: translateX(-50%);'>"
            "当前浏览器类型不在支持范围内，支持的浏览器类型有：{}</div>"
        ).format(
            "、".join([rule["browser"] for rule in BaseConfig.min_browser_versions])
        )

    return None


@app.server.middleware("http")
async def load_auth_and_check_browser(request: Request, call_next):
    browser_block_message = _browser_block_message(request)
    if browser_block_message:
        return HTMLResponse(browser_block_message)

    if _should_skip_auth(request.url.path):
        request.state.current_user = AnonymousUser()
    else:
        request.state.current_user = await manager.optional(request) or AnonymousUser()

    return await call_next(request)
