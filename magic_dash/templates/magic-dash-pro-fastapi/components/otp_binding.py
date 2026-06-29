from dash import set_props, dcc
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style
from dash.dependencies import Input, State

from server import app, current_user
from configs import BaseConfig
from models.otp_credentials import OtpCredentials
from models.users import Users
from utils.otp_utils import (
    build_otp_provisioning_uri,
    encrypt_otp_secret,
    generate_otp_secret,
    verify_otp_code,
)


def render():
    """渲染OTP绑定模态框"""

    return fac.AntdModal(
        id="otp-binding-modal",
        title=fac.AntdSpace([fac.AntdIcon(icon="antd-safety-certificate"), "OTP绑定"]),
        renderFooter=False,
        width=440,
        destroyOnClose=True,
    )


def build_otp_binding_content():
    """构建OTP绑定内容"""

    if not BaseConfig.enable_otp_login:
        return fac.AntdAlert(
            message="当前未启用OTP动态口令登录功能。",
            type="info",
            showIcon=True,
        )

    try:
        match_user = Users.get_user(current_user.id)
        if not match_user:
            raise ValueError("当前用户信息不存在")

        otp_secret = generate_otp_secret()
        provisioning_uri = build_otp_provisioning_uri(match_user.user_name, otp_secret)
        otp_enabled = OtpCredentials.has_enabled_otp(current_user.id)
    except Exception:
        app.server.logger.exception("OTP绑定二维码生成失败")
        return fac.AntdAlert(
            message="OTP绑定服务异常，请检查依赖安装和配置参数后重试。",
            type="error",
            showIcon=True,
        )

    return [
        dcc.Store(id="otp-binding-secret", data=otp_secret),
        fac.AntdSpace(
            [
                fac.AntdAlert(
                    message=(
                        "当前账号已绑定OTP动态口令，确认后将使用新的二维码覆盖旧绑定。"
                        if otp_enabled
                        else "请使用认证器App扫描二维码，完成添加后输入当前6位动态口令。"
                    ),
                    type="warning" if otp_enabled else "info",
                    showIcon=True,
                ),
                fac.AntdCenter(
                    fac.AntdQRCode(
                        value=provisioning_uri,
                        type="svg",
                        size=220,
                        bordered=True,
                        errorLevel="M",
                    ),
                    style=style(width="100%", paddingTop=8, paddingBottom=8),
                ),
                fac.AntdFormItem(
                    fac.AntdOTP(
                        id="otp-binding-code",
                        size="large",
                        length=6,
                    ),
                    id="otp-binding-code-form-item",
                    label="输入认证器App中的6位动态口令",
                    layout="vertical",
                ),
                fac.AntdFlex(
                    [
                        fac.AntdButton(
                            "取消",
                            id="otp-binding-cancel",
                        ),
                        fac.AntdButton(
                            "确认绑定",
                            id="otp-binding-confirm",
                            type="primary",
                            autoSpin=True,
                        ),
                    ],
                    justify="end",
                    gap=8,
                ),
            ],
            direction="vertical",
            style=style(width="100%", paddingTop=8),
        ),
    ]


@app.callback(
    Input("otp-binding-cancel", "nClicks"),
    prevent_initial_call=True,
)
def close_otp_binding_modal(nClicks):
    """关闭OTP绑定模态框"""

    if not nClicks:
        return

    set_props("otp-binding-modal", {"visible": False})


@app.callback(
    Input("otp-binding-confirm", "nClicks"),
    [
        State("otp-binding-secret", "data"),
        State("otp-binding-code", "value"),
    ],
    prevent_initial_call=True,
)
def confirm_otp_binding(nClicks, otp_secret, otp_code):
    """确认绑定OTP动态口令"""

    if not nClicks:
        return

    if not BaseConfig.enable_otp_login:
        return

    otp_code = str(otp_code or "").strip()
    if len(otp_code) != 6 or not otp_code.isdigit():
        set_props(
            "otp-binding-code-form-item",
            {"help": "请输入6位数字动态口令", "validateStatus": "error"},
        )
        set_props("otp-binding-confirm", {"loading": False})
        return

    try:
        is_valid, _ = verify_otp_code(otp_secret, otp_code)
    except Exception:
        app.server.logger.exception("OTP绑定动态口令校验失败")
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="OTP绑定服务异常，请稍后重试",
                )
            },
        )
        set_props("otp-binding-confirm", {"loading": False})
        return

    if not is_valid:
        set_props(
            "otp-binding-code-form-item",
            {
                "help": "动态口令错误，请确认认证器时间同步后重试",
                "validateStatus": "error",
            },
        )
        set_props("otp-binding-confirm", {"loading": False})
        return

    try:
        OtpCredentials.enable_credential(
            current_user.id,
            encrypt_otp_secret(otp_secret),
        )
    except Exception:
        app.server.logger.exception("OTP动态口令凭据保存失败")
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="OTP动态口令凭据保存失败，请稍后重试",
                )
            },
        )
        set_props("otp-binding-confirm", {"loading": False})
        return

    set_props("otp-binding-modal", {"visible": False})
    set_props(
        "global-message",
        {
            "children": fac.AntdMessage(
                type="success",
                content="OTP动态口令绑定成功",
            )
        },
    )
    set_props("otp-binding-confirm", {"loading": False})
