import uuid
import time
import dash
from flask import request
from datetime import datetime
from user_agents import parse
from dash import set_props, dcc
from flask_login import login_user
import feffery_antd_components as fac
import feffery_utils_components as fuc
from feffery_dash_utils.style_utils import style
from flask_principal import identity_changed, Identity
from dash.dependencies import Input, Output, State, ClientsideFunction

from server import app, User
from models.users import Users
from configs import BaseConfig, EmailConfig, OtpConfig
from models.email_verifications import EmailVerifications
from models.logs import LoginLogs
from models.otp_credentials import OtpCredentials
from utils.crypto_utils import restore_login_password
from utils.email_utils import send_email_verification_code
from utils.otp_utils import decrypt_otp_secret, verify_otp_code
from utils.validation_utils import validate_optional_email


def complete_user_login(match_user, remember=False):
    """为已完成身份校验的用户建立登录会话"""

    new_session_token = str(uuid.uuid4())
    Users.update_user(match_user.user_id, session_token=new_session_token)

    new_user = User(
        id=match_user.user_id,
        user_name=match_user.user_name,
        user_role=match_user.user_role,
        session_token=new_session_token,
    )

    login_user(new_user, remember=remember)
    dash.ctx.response.set_cookie(
        BaseConfig.session_token_cookie_name,
        new_session_token,
    )
    identity_changed.send(app.server, identity=Identity(new_user.id))
    set_props(
        "global-redirect",
        {"children": dcc.Location(pathname="/", id="global-redirect-target")},
    )


app.clientside_callback(
    # 基于浏览器内置Web Crypto API加密密码
    ClientsideFunction(namespace="clientside_basic", function_name="encryptPassword"),
    Output("login-password-crypto", "data"),
    Input("login-password", "value"),
    State("login-rsa-pubkey", "data"),
    State("login-rsa-crypto-enabled", "data"),
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
        State("login-slider-captcha", "verifyResult", allow_optional=True),
    ],
    running=[
        [Output("login-button", "loading"), True, False],
    ],
    prevent_initial_call=True,
)
def handle_login(
    nClicks, nSubmit, user_name, password_crypto, remember_me, slider_verify_result
):
    """处理用户登录逻辑"""

    time.sleep(0.25)

    # 还原前端传输的密码字段值
    password = restore_login_password(
        password_crypto, BaseConfig.enable_login_rsa_crypto
    )

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

    # 处理滑块验证启用场景
    if BaseConfig.enable_login_captcha:
        # 验证通过
        if slider_verify_result and slider_verify_result.get("status") == "success":
            pass
        else:
            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="error",
                        content="请先完成滑块验证",
                    )
                },
            )

            return [None] * 4

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

        complete_user_login(match_user, remember=remember_me)

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


@app.callback(
    Input("login-more-options-trigger", "nClicks"),
    State("login-more-options-trigger", "clickedKey"),
    prevent_initial_call=True,
)
def render_more_login_modal(nClicks, clickedKey):
    """处理更多登录方式对应模态框的挂载"""

    if BaseConfig.enable_email_login and clickedKey == "email":
        set_props(
            "login-more-options-modal-target",
            {
                "key": str(uuid.uuid4()),  # 强制刷新
                "children": fac.AntdModal(
                    [
                        fac.AntdForm(
                            [
                                # 邮箱地址
                                fac.AntdFormItem(
                                    fac.AntdInput(
                                        id="login-user-email",
                                        placeholder="请输入合法用户关联邮箱地址",
                                        size="large",
                                        prefix=fac.AntdIcon(
                                            icon="antd-mail",
                                            className="global-help-text",
                                        ),
                                        autoComplete="off",
                                    ),
                                    id="login-user-email-form-item",
                                    label="邮箱地址",
                                    style=style(marginBottom=18),
                                ),
                                # 动态验证码
                                fac.AntdFormItem(
                                    fac.AntdFlex(
                                        [
                                            fac.AntdOTP(
                                                id="login-user-email-captcha",
                                                size="large",
                                                length=6,
                                                style=style(flex=1),
                                            ),
                                            fac.AntdButton(
                                                "获取验证码",
                                                id="login-user-email-captcha-send",
                                                type="primary",
                                                size="large",
                                                autoSpin=True,
                                                loadingChildren="处理中",
                                                style=style(width=128),
                                            ),
                                        ],
                                        gap=8,
                                    ),
                                    id="login-user-email-captcha-form-item",
                                    label="动态验证码",
                                    style=style(marginBottom=12),
                                ),
                                fac.AntdButton(
                                    "登录",
                                    id="login-user-email-submit",
                                    type="primary",
                                    block=True,
                                    size="large",
                                    autoSpin=True,
                                    style=style(marginTop=24),
                                ),
                            ],
                            layout="vertical",
                            style=style(paddingTop=8),
                        ),
                        # 邮箱验证登录其他辅助组件
                        fac.Fragment(
                            [
                                # 重复发送验证码倒计时
                                fuc.FefferyCountDown(
                                    id="login-user-email-captcha-retry-countdown",
                                    interval=1,
                                )
                            ]
                        ),
                    ],
                    title=fac.AntdSpace(
                        [fac.AntdIcon(icon="antd-mail"), "邮箱验证登录"]
                    ),
                    visible=True,
                    renderFooter=False,
                    width=480,
                    centered=True,
                ),
            },
        )

    elif BaseConfig.enable_otp_login and clickedKey == "otp":
        set_props(
            "login-more-options-modal-target",
            {
                "key": str(uuid.uuid4()),  # 强制刷新
                "children": fac.AntdModal(
                    [
                        fac.AntdForm(
                            [
                                # 用户名
                                fac.AntdFormItem(
                                    fac.AntdInput(
                                        id="login-user-otp-name",
                                        placeholder="请输入用户名",
                                        size="large",
                                        prefix=fac.AntdIcon(
                                            icon="antd-user",
                                            className="global-help-text",
                                        ),
                                        autoComplete="off",
                                    ),
                                    id="login-user-otp-name-form-item",
                                    label="用户名",
                                    style=style(marginBottom=18),
                                ),
                                # 6位动态口令
                                fac.AntdFormItem(
                                    fac.AntdCenter(
                                        fac.AntdOTP(
                                            id="login-user-otp-code",
                                            size="large",
                                            length=6,
                                        )
                                    ),
                                    id="login-user-otp-code-form-item",
                                    label="6位动态口令",
                                    style=style(marginBottom=12),
                                ),
                                fac.AntdButton(
                                    "登录",
                                    id="login-user-otp-submit",
                                    type="primary",
                                    block=True,
                                    size="large",
                                    autoSpin=True,
                                    style=style(marginTop=24),
                                ),
                            ],
                            layout="vertical",
                            style=style(paddingTop=8),
                        )
                    ],
                    title=fac.AntdSpace(
                        [
                            fac.AntdIcon(icon="antd-safety-certificate"),
                            "OTP动态口令登录",
                        ]
                    ),
                    visible=True,
                    renderFooter=False,
                    width=480,
                    centered=True,
                ),
            },
        )


@app.callback(
    Input("login-user-email-captcha-send", "nClicks"),
    State("login-user-email", "value"),
    prevent_initial_call=True,
)
def send_login_user_email_captcha(nClicks, email):
    """处理登录邮箱验证码发送逻辑"""

    if not BaseConfig.enable_email_login:
        # 提前终止当前无输出回调
        return

    email = (email or "").strip()

    if not email or not validate_optional_email(email):
        set_props(
            "login-user-email-form-item",
            {"help": "请输入有效邮箱地址", "validateStatus": "error"},
        )
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="请输入有效邮箱地址",
                )
            },
        )
        set_props(
            "login-user-email-captcha-send",
            {"children": "获取验证码", "loading": False, "disabled": False},
        )
        # 提前终止当前无输出回调
        return

    expire_seconds = EmailConfig.verification_code_expire_seconds
    resend_interval_seconds = EmailConfig.verification_code_resend_interval_seconds

    if (
        not isinstance(expire_seconds, int)
        or expire_seconds <= 0
        or not isinstance(resend_interval_seconds, int)
        or resend_interval_seconds <= 0
        or resend_interval_seconds > expire_seconds
    ):
        app.server.logger.error("邮箱验证码有效期或重复发送等待时间配置不正确")
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="邮箱验证码服务配置异常，请联系管理员",
                )
            },
        )
        set_props(
            "login-user-email-captcha-send",
            {"children": "获取验证码", "loading": False, "disabled": False},
        )
        # 提前终止当前无输出回调
        return

    try:
        match_user = Users.get_user_by_email(email)
    except Exception:
        app.server.logger.exception("邮箱登录用户信息查询失败")
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="用户信息查询失败，请稍后重试",
                )
            },
        )
        set_props(
            "login-user-email-captcha-send",
            {"children": "获取验证码", "loading": False, "disabled": False},
        )
        # 提前终止当前无输出回调
        return

    if not match_user:
        set_props(
            "login-user-email-form-item",
            {"help": "该邮箱未关联有效用户", "validateStatus": "error"},
        )
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="该邮箱未关联有效用户",
                )
            },
        )
        set_props(
            "login-user-email-captcha-send",
            {"children": "获取验证码", "loading": False, "disabled": False},
        )
        # 提前终止当前无输出回调
        return

    try:
        (
            verification,
            remaining_seconds,
            previous_verification,
        ) = EmailVerifications.issue_verification(
            email,
            resend_interval_seconds,
        )
    except Exception:
        app.server.logger.exception("邮箱登录验证码签发失败")
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="验证码生成失败，请稍后重试",
                )
            },
        )
        set_props(
            "login-user-email-captcha-send",
            {"children": "获取验证码", "loading": False, "disabled": False},
        )
        # 提前终止当前无输出回调
        return

    if remaining_seconds > 0:
        set_props(
            "login-user-email-captcha-retry-countdown",
            {"delay": remaining_seconds, "key": str(uuid.uuid4())},
        )
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="warning",
                    content=f"请在{remaining_seconds}秒后重新获取验证码",
                )
            },
        )
        set_props(
            "login-user-email-captcha-send",
            {"loading": False},
        )
        # 提前终止当前无输出回调
        return

    try:
        send_email_verification_code(email, verification.verification_code)
    except Exception:
        app.server.logger.exception("邮箱登录验证码发送失败")
        try:
            EmailVerifications.rollback_issued_verification(
                verification,
                previous_verification,
            )
        except Exception:
            app.server.logger.exception("发送失败后的邮箱验证码清理失败")
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="验证码发送失败，请检查邮件服务配置后重试",
                )
            },
        )
        set_props(
            "login-user-email-captcha-send",
            {"children": "获取验证码", "loading": False, "disabled": False},
        )
        # 提前终止当前无输出回调
        return

    set_props(
        "login-user-email-form-item",
        {"help": None, "validateStatus": "success"},
    )
    set_props("login-user-email-captcha", {"value": ""})
    set_props(
        "login-user-email-captcha-form-item",
        {"help": None, "validateStatus": None},
    )
    set_props(
        "login-user-email-captcha-retry-countdown",
        {"delay": resend_interval_seconds, "key": str(uuid.uuid4())},
    )
    set_props(
        "login-user-email-captcha-send",
        {"loading": False},
    )
    set_props(
        "global-message",
        {
            "children": fac.AntdMessage(
                type="success",
                content="验证码已发送，请注意查收",
            )
        },
    )


app.clientside_callback(
    # 处理邮箱验证码发送后按钮的倒计时状态更新
    """
(countdown) => {
    if (!countdown || countdown <= 0) {
        return ["获取验证码", false];
    }
    return [`${countdown}秒后重发`, true];
}
""",
    [
        Output("login-user-email-captcha-send", "children"),
        Output("login-user-email-captcha-send", "disabled"),
    ],
    Input("login-user-email-captcha-retry-countdown", "countdown"),
)


@app.callback(
    Input("login-user-email-submit", "nClicks"),
    [
        State("login-user-email", "value"),
        State("login-user-email-captcha", "value"),
    ],
    prevent_initial_call=True,
)
def handle_login_user_email_submit(nClicks, email, verification_code):
    """处理邮箱验证码校验及登录逻辑"""

    if not BaseConfig.enable_email_login:
        # 提前终止当前无输出回调
        return

    email = (email or "").strip()
    verification_code = str(verification_code or "").strip()

    if not email or not validate_optional_email(email):
        set_props(
            "login-user-email-form-item",
            {"help": "请输入有效邮箱地址", "validateStatus": "error"},
        )
        set_props("login-user-email-submit", {"loading": False})
        # 提前终止当前无输出回调
        return

    if len(verification_code) != 6 or not verification_code.isdigit():
        set_props(
            "login-user-email-captcha-form-item",
            {"help": "请输入6位数字验证码", "validateStatus": "error"},
        )
        set_props("login-user-email-submit", {"loading": False})
        # 提前终止当前无输出回调
        return

    try:
        match_user = Users.get_user_by_email(email)
    except Exception:
        app.server.logger.exception("邮箱登录用户信息查询失败")
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="用户信息查询失败，请稍后重试",
                )
            },
        )
        set_props("login-user-email-submit", {"loading": False})
        # 提前终止当前无输出回调
        return

    if not match_user:
        set_props(
            "login-user-email-form-item",
            {"help": "邮箱或验证码错误", "validateStatus": "error"},
        )
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="邮箱或验证码错误",
                )
            },
        )
        set_props("login-user-email-submit", {"loading": False})
        # 提前终止当前无输出回调
        return

    try:
        verify_result = EmailVerifications.verify_code(
            email,
            verification_code,
            EmailConfig.verification_code_expire_seconds,
        )
    except Exception:
        app.server.logger.exception("邮箱登录验证码校验失败")
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="验证码校验服务异常，请稍后重试",
                )
            },
        )
        set_props("login-user-email-submit", {"loading": False})
        # 提前终止当前无输出回调
        return

    verify_result_messages = {
        "not_found": "邮箱或验证码错误",
        "expired": "验证码已过期，请重新获取",
        "invalid": "邮箱或验证码错误",
    }

    if verify_result != "valid":
        error_message = verify_result_messages.get(verify_result, "验证码校验失败")
        set_props(
            "login-user-email-captcha-form-item",
            {"help": error_message, "validateStatus": "error"},
        )
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content=error_message,
                )
            },
        )
        set_props("login-user-email-submit", {"loading": False})

        user_agent = parse(str(request.user_agent))
        LoginLogs.add_log(
            user_name=match_user.user_name,
            user_id=match_user.user_id,
            ip=request.remote_addr,
            browser="{} {}".format(
                user_agent.browser.family,
                user_agent.browser.version_string,
            ),
            os="{} {}".format(user_agent.os.family, user_agent.os.version_string),
            status=error_message,
            login_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        # 提前终止当前无输出回调
        return

    set_props(
        "login-user-email-captcha-form-item",
        {"help": None, "validateStatus": "success"},
    )
    set_props("login-user-email-submit", {"loading": False})
    complete_user_login(match_user)

    user_agent = parse(str(request.user_agent))
    LoginLogs.add_log(
        user_name=match_user.user_name,
        user_id=match_user.user_id,
        ip=request.remote_addr,
        browser="{} {}".format(
            user_agent.browser.family,
            user_agent.browser.version_string,
        ),
        os="{} {}".format(user_agent.os.family, user_agent.os.version_string),
        status="邮箱登录成功",
        login_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


@app.callback(
    Input("login-user-otp-submit", "nClicks"),
    [
        State("login-user-otp-name", "value"),
        State("login-user-otp-code", "value"),
    ],
    prevent_initial_call=True,
)
def handle_login_user_otp_submit(nClicks, user_name, otp_code):
    """处理OTP动态口令校验及登录逻辑"""

    if not BaseConfig.enable_otp_login:
        # 提前终止当前无输出回调
        return

    user_name = (user_name or "").strip()
    otp_code = str(otp_code or "").strip()

    if not user_name:
        set_props(
            "login-user-otp-name-form-item",
            {"help": "请输入用户名", "validateStatus": "error"},
        )
        set_props("login-user-otp-submit", {"loading": False})
        return

    if len(otp_code) != 6 or not otp_code.isdigit():
        set_props(
            "login-user-otp-code-form-item",
            {"help": "请输入6位数字动态口令", "validateStatus": "error"},
        )
        set_props("login-user-otp-submit", {"loading": False})
        return

    user_agent = parse(str(request.user_agent))
    browser_info = "{} {}".format(
        user_agent.browser.family,
        user_agent.browser.version_string,
    )
    os_info = "{} {}".format(user_agent.os.family, user_agent.os.version_string)

    def reject_login(match_user=None, message="用户名或动态口令错误"):
        """统一处理OTP登录失败反馈与日志"""

        set_props(
            "login-user-otp-code-form-item",
            {"help": message, "validateStatus": "error"},
        )
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content=message,
                )
            },
        )
        set_props("login-user-otp-submit", {"loading": False})

        LoginLogs.add_log(
            user_name=match_user.user_name if match_user else user_name,
            user_id=match_user.user_id if match_user else None,
            ip=request.remote_addr,
            browser=browser_info,
            os=os_info,
            status=message,
            login_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    try:
        match_user = Users.get_user_by_name(user_name)
    except Exception:
        app.server.logger.exception("OTP登录用户信息查询失败")
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="用户信息查询失败，请稍后重试",
                )
            },
        )
        set_props("login-user-otp-submit", {"loading": False})
        return

    if not match_user:
        reject_login()
        return

    credential = OtpCredentials.get_credential(match_user.user_id)

    if not credential or not credential.is_enabled:
        reject_login(match_user)
        return

    if OtpCredentials.is_locked(credential):
        reject_login(match_user, "尝试次数过多，请稍后再试")
        return

    try:
        otp_secret = decrypt_otp_secret(credential.secret_ciphertext)
        is_valid, timecode = verify_otp_code(otp_secret, otp_code)
    except Exception:
        app.server.logger.exception("OTP动态口令校验失败")
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="OTP动态口令服务异常，请稍后重试",
                )
            },
        )
        set_props("login-user-otp-submit", {"loading": False})
        return

    if not is_valid:
        OtpCredentials.record_failed_attempt(
            match_user.user_id,
            OtpConfig.max_failed_attempts,
            OtpConfig.lockout_seconds,
        )
        reject_login(match_user)
        return

    if (
        credential.last_used_timecode is not None
        and timecode <= credential.last_used_timecode
    ):
        OtpCredentials.record_failed_attempt(
            match_user.user_id,
            OtpConfig.max_failed_attempts,
            OtpConfig.lockout_seconds,
        )
        reject_login(match_user, "动态口令已失效，请等待下一组口令")
        return

    OtpCredentials.mark_used(match_user.user_id, timecode)
    set_props(
        "login-user-otp-code-form-item",
        {"help": None, "validateStatus": "success"},
    )
    set_props("login-user-otp-submit", {"loading": False})
    complete_user_login(match_user)

    LoginLogs.add_log(
        user_name=match_user.user_name,
        user_id=match_user.user_id,
        ip=request.remote_addr,
        browser=browser_info,
        os=os_info,
        status="OTP登录成功",
        login_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
