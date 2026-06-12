from dash import html, dcc
import feffery_antd_components as fac
import feffery_utils_components as fuc
from feffery_dash_utils.style_utils import style

from configs import BaseConfig, LayoutConfig
from utils.crypto_utils import rsa_public_key

# 令绑定的回调函数子模块生效
import callbacks.login_c  # noqa: F401


def render():
    """渲染用户登录页面"""

    # 登录页内容素材区：根据配置在插图动效、视频背景与渐变色背景之间切换
    if LayoutConfig.login_content_type == "image":
        login_content = [
            fuc.FefferyMotion(
                html.Img(
                    src="/assets/imgs/login/插图1.svg",
                    style=style(width="25vw"),
                ),
                style={
                    "position": "absolute",
                    "left": "10%",
                    "top": "15%",
                    "rotateZ": "-5deg",
                },
                animate={"y": [25, -25, 25]},
                transition={
                    "duration": 4.5,
                    "repeat": "infinity",
                    "type": "spring",
                },
            ),
            fuc.FefferyMotion(
                html.Img(
                    src="/assets/imgs/login/插图2.svg",
                    style=style(width="15vw"),
                ),
                style={
                    "position": "absolute",
                    "right": "20%",
                    "top": "25%",
                    "rotateZ": "15deg",
                },
                animate={"y": [-15, 15, -15]},
                transition={
                    "duration": 5.5,
                    "repeat": "infinity",
                    "type": "spring",
                },
            ),
            fuc.FefferyMotion(
                html.Img(
                    src="/assets/imgs/login/插图3.svg",
                    style=style(width="12vw"),
                ),
                style={
                    "position": "absolute",
                    "left": "25%",
                    "bottom": "25%",
                    "rotateZ": "-8deg",
                },
                animate={"y": [10, -10, 10]},
                transition={
                    "duration": 5,
                    "repeat": "infinity",
                    "type": "spring",
                },
            ),
            fuc.FefferyMotion(
                html.Img(
                    src="/assets/imgs/login/插图4.svg",
                    style=style(width="25vw"),
                ),
                style={
                    "position": "absolute",
                    "right": "15%",
                    "bottom": "8%",
                    "rotateZ": "5deg",
                },
                animate={"y": [20, -20, 20]},
                transition={
                    "duration": 6,
                    "repeat": "infinity",
                    "type": "spring",
                },
            ),
        ]
    elif LayoutConfig.login_content_type == "video":
        login_content = [
            html.Video(
                src="/assets/videos/login-bg.mp4",
                autoPlay=True,
                muted=True,
                loop=True,
                className="login-content-video",
            )
        ]
    else:
        # 渐变内容区由CSS统一承载背景图与循环动效，三种登录布局共用
        login_content = [html.Div(className="login-gradient-content-bg")]

    # 登录控件区：在居中布局中由AntdCenter承担玻璃拟态容器样式
    login_form = fac.AntdCenter(
        [
            html.Div(
                fac.AntdSpace(
                    [
                        html.Img(
                            src="/assets/imgs/magic-dash-logo.svg",
                            height=96,
                        ),
                        fac.AntdText(
                            BaseConfig.app_title,
                            className="login-app-title",
                            style=style(fontSize=36),
                        ),
                        fac.AntdForm(
                            [
                                # 存储RSA公钥（从文件读取初始值）
                                dcc.Store(id="login-rsa-pubkey", data=rsa_public_key),
                                # 存储当前项目是否启用登录密码RSA加密
                                dcc.Store(
                                    id="login-rsa-crypto-enabled",
                                    data=BaseConfig.enable_login_rsa_crypto,
                                ),
                                # 存储加密后的密码
                                dcc.Store(id="login-password-crypto"),
                                fac.AntdFormItem(
                                    fac.AntdInput(
                                        id="login-user-name",
                                        placeholder="请输入用户名",
                                        size="large",
                                        prefix=fac.AntdIcon(
                                            icon="antd-user",
                                            className="global-help-text",
                                        ),
                                        autoComplete="off",
                                    ),
                                    id="login-user-name-form-item",
                                    label="用户名",
                                ),
                                fac.AntdFormItem(
                                    fac.AntdInput(
                                        id="login-password",
                                        placeholder="请输入密码",
                                        size="large",
                                        mode="password",
                                        prefix=fac.AntdIcon(
                                            icon="antd-lock",
                                            className="global-help-text",
                                        ),
                                    ),
                                    id="login-password-form-item",
                                    label="密码",
                                ),
                                (
                                    fac.AntdFormItem(
                                        fuc.FefferySliderCaptcha(
                                            id="login-slider-captcha",
                                            block=True,
                                            mode="slider",
                                            tipText={
                                                "default": "请按住滑块，拖动到最右边",
                                                "moving": "请按住滑块，拖动到最右边",
                                                "error": "验证失败，请重新操作",
                                                "success": "验证成功",
                                            },
                                            style=style(width="100%"),
                                        )
                                    )
                                    if BaseConfig.enable_login_captcha
                                    else None
                                ),
                                fac.AntdCheckbox(
                                    id="login-remember-me", label="记住我"
                                ),
                                fac.AntdButton(
                                    "登录",
                                    id="login-button",
                                    loadingChildren="校验中",
                                    type="primary",
                                    block=True,
                                    size="large",
                                    style=style(marginTop=18),
                                ),
                            ],
                            layout="vertical",
                            style=style(width=350),
                        ),
                    ],
                    direction="vertical",
                    align="center",
                ),
                className="login-form-panel",
            )
        ],
        className=(
            f"login-form-center login-form-center-{LayoutConfig.login_page_layout}"
        ),
        style=style(
            height=(
                "auto"
                if LayoutConfig.login_page_layout == "centered"
                else "calc(100% - 200px)"
            )
        ),
    )

    # 常规左右分栏布局中的内容半区
    content_side = fac.AntdCol(
        login_content,
        span=14,
        className=(
            "login-left-side login-content-side "
            f"login-content-side-{LayoutConfig.login_page_layout}"
        ),
        style=(
            style()
            if LayoutConfig.login_content_type == "image"
            else style(backgroundImage="none")
        ),
    )

    # 常规左右分栏布局中的登录控件半区
    form_side = fac.AntdCol(
        login_form,
        span=10,
        className=(
            "login-right-side login-form-side "
            f"login-form-side-{LayoutConfig.login_page_layout}"
        ),
    )

    if LayoutConfig.login_page_layout == "centered":
        # 居中布局：内容素材铺满作为背景，登录控件悬浮居中
        return html.Div(
            [
                html.Div(
                    login_content,
                    className=(
                        "login-left-side login-content-side "
                        f"login-content-side-{LayoutConfig.login_page_layout}"
                    ),
                    style=(
                        style()
                        if LayoutConfig.login_content_type == "image"
                        else style(backgroundImage="none")
                    ),
                ),
                html.Div(login_form, className="login-centered-form-layer"),
            ],
            className="login-page login-page-centered",
            style=style(height="100vh"),
        )

    if LayoutConfig.login_page_layout == "form-left":
        # 左侧登录控件、右侧内容素材布局
        return fac.AntdRow(
            [form_side, content_side],
            wrap=False,
            className="login-page login-page-form-left",
            style=style(height="100vh"),
        )

    # 默认布局：左侧内容素材、右侧登录控件
    return fac.AntdRow(
        [content_side, form_side],
        wrap=False,
        className="login-page login-page-content-left",
        style=style(height="100vh"),
    )
