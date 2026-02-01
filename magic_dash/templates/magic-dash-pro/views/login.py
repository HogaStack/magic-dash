from dash import html, dcc
import feffery_antd_components as fac
import feffery_utils_components as fuc
from feffery_dash_utils.style_utils import style

from configs import BaseConfig, LayoutConfig
from utils.crypto_utils import load_rsa_public_key

# 令绑定的回调函数子模块生效
import callbacks.login_c  # noqa: F401


def render():
    """渲染用户登录页面"""

    # 加载RSA公钥
    rsa_public_key = load_rsa_public_key()

    return fac.AntdRow(
        [
            # 左侧半边
            fac.AntdCol(
                *(
                    [
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
                    if LayoutConfig.login_left_side_content_type == "image"
                    else [
                        html.Video(
                            src="/assets/videos/login-bg.mp4",
                            autoPlay=True,
                            muted=True,
                            loop=True,
                            style=style(
                                width="100%",
                                height="100%",
                                position="absolute",
                                objectFit="cover",
                                borderTopRightRadius=12,
                                borderBottomRightRadius=12,
                                pointerEvents="none",
                            ),
                        )
                    ],
                ),
                span=14,
                className="login-left-side",
                style=(
                    style()
                    if LayoutConfig.login_left_side_content_type == "image"
                    else style(backgroundImage="none")
                ),
            ),
            # 右侧半边
            fac.AntdCol(
                fac.AntdCenter(
                    [
                        fac.AntdSpace(
                            [
                                html.Img(
                                    src="/assets/imgs/logo.svg",
                                    height=72,
                                ),
                                fac.AntdText(
                                    BaseConfig.app_title,
                                    style=style(fontSize=36),
                                ),
                                fac.AntdForm(
                                    [
                                        # 存储RSA公钥（从文件读取初始值）
                                        dcc.Store(
                                            id="login-rsa-pubkey", data=rsa_public_key
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
                        )
                    ],
                    style=style(height="calc(100% - 200px)"),
                ),
                span=10,
                className="login-right-side",
            ),
        ],
        wrap=False,
        style=style(height="100vh"),
    )
