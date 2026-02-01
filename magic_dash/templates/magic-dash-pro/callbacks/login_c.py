import uuid
import time
import dash
from flask import request
from datetime import datetime
from user_agents import parse
from dash import set_props, dcc
from flask_login import login_user
import feffery_antd_components as fac
from flask_principal import identity_changed, Identity
from dash.dependencies import Input, Output, State, ClientsideFunction

from server import app, User
from models.users import Users
from configs import BaseConfig
from models.logs import LoginLogs
from utils.crypto_utils import decrypt_password


app.clientside_callback(
    # 基于浏览器内置Web Crypto API加密密码
    ClientsideFunction(namespace="clientside_basic", function_name="encryptPassword"),
    Output("login-password-crypto", "data"),
    Input("login-password", "value"),
    State("login-rsa-pubkey", "data"),
)


@app.callback(
    [
        Output("login-user-name-form-item", "help"),
        Output("login-password-form-item", "help"),
        Output("login-user-name-form-item", "validateStatus"),
        Output("login-password-form-item", "validateStatus"),
    ],
    [Input("login-button", "nClicks"), Input("login-password", "nSubmit")],
    [
        State("login-user-name", "value"),
        State("login-password-crypto", "data"),
        State("login-remember-me", "checked"),
    ],
    running=[
        [Output("login-button", "loading"), True, False],
    ],
    prevent_initial_call=True,
)
def handle_login(nClicks, nSubmit, user_name, password_crypto, remember_me):
    """处理用户登录逻辑"""

    time.sleep(0.25)

    # 解密前端传输的加密密码
    password = decrypt_password(password_crypto)

    # 构造兼容原有判断逻辑的表单values
    values = {
        "login-user-name": user_name,
        "login-password": password,
    }

    # 提取当前登录行为对应的系统、浏览器信息
    user_agent = parse(str(request.user_agent))
    # 系统信息
    os_info = "{} {}".format(user_agent.os.family, user_agent.os.version_string)
    # 浏览器信息
    browser_info = "{} {}".format(
        user_agent.browser.family, user_agent.browser.version[0]
    )

    # 若表单必要信息不完整
    if not (values.get("login-user-name") and values.get("login-password")):
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="请完善登录信息",
                )
            },
        )

        return [
            # 表单帮助信息
            "请输入用户名" if not values.get("login-user-name") else None,
            "请输入密码" if not values.get("login-password") else None,
            # 表单帮助状态
            "error" if not values.get("login-user-name") else None,
            "error" if not values.get("login-password") else None,
        ]

    # 校验用户登录信息

    # 根据用户名尝试查询用户
    match_user = Users.get_user_by_name(values["login-user-name"])

    # 若用户不存在
    if not match_user:
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="用户不存在",
                )
            },
        )

        # 登录日志记录
        LoginLogs.add_log(
            user_name=values["login-user-name"],
            user_id=None,  # 不存在的用户无id
            ip=request.remote_addr,
            browser=browser_info,
            os=os_info,
            status="用户不存在",
            login_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        return [
            # 表单帮助信息
            "用户不存在",
            None,
            # 表单帮助状态
            "error",
            None,
        ]

    else:
        # 校验密码

        # 若密码不正确
        if not Users.check_user_password(match_user.user_id, values["login-password"]):
            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="error",
                        content="密码错误",
                    )
                },
            )

            # 登录日志记录
            LoginLogs.add_log(
                user_name=values["login-user-name"],
                user_id=match_user.user_id,
                ip=request.remote_addr,
                browser=browser_info,
                os=os_info,
                status="密码错误",
                login_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

            return [
                # 表单帮助信息
                None,
                "密码错误",
                # 表单帮助状态
                None,
                "error",
            ]

        # 更新用户信息表session_token字段
        new_session_token = str(uuid.uuid4())
        Users.update_user(match_user.user_id, session_token=new_session_token)

        # 进行用户登录
        new_user = User(
            id=match_user.user_id,
            user_name=match_user.user_name,
            user_role=match_user.user_role,
            session_token=new_session_token,
        )

        # 会话登录状态切换
        login_user(new_user, remember=remember_me)

        # 在cookies更新ession_token字段
        dash.ctx.response.set_cookie(
            BaseConfig.session_token_cookie_name, new_session_token
        )

        # 更新用户身份信息
        identity_changed.send(app.server, identity=Identity(new_user.id))

        # 重定向至首页
        set_props(
            "global-redirect",
            {"children": dcc.Location(pathname="/", id="global-redirect-target")},
        )

        # 登录日志记录
        LoginLogs.add_log(
            user_name=match_user.user_name,
            user_id=match_user.user_id,
            ip=request.remote_addr,
            browser=browser_info,
            os=os_info,
            status="登录成功",
            login_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    return [None] * 4
