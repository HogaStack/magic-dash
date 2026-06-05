from typing import List, Union, Callable


class BaseConfig:
    """应用基础配置参数"""

    # 应用基础标题
    app_title: str = "Magic Dash Pro"

    # 应用版本
    app_version: str = "dev"

    # 是否启用版本更新日志通知功能，每次的新版本更新日志将在用户点击“已阅”按钮后不再重复展示
    enable_version_changelog_modal: bool = False

    # 设置版本更新日志通知对应的markdown文件所在目录，目录下文件名格式应为“版本号.md”
    version_changelog_markdown_folder: str = "changelogs"

    # 应用密钥，fastapi-login基于此密钥签发JWT，建议长度不低于32字节
    app_secret_key: str = "magic-dash-pro-fastapi-demo-secret-key"

    # 应用会话cookie名称
    # 由于同一主机地址下的不同端口，在浏览器中会
    # 共享cookies，因此在同一主机地址下部署多套基于
    # magic-dash-pro模板开发的独立项目时，请为各个项目
    # 设置不同的app_session_cookie_name
    app_session_cookie_name: str = "magic_dash_pro_fastapi_session"

    # 登录会话有效期，单位：秒
    login_session_expire_seconds: int = 12 * 60 * 60

    # 勾选“记住我”后的登录会话有效期，单位：秒
    remember_login_expire_seconds: int = 30 * 24 * 60 * 60

    # 浏览器最低版本限制规则
    min_browser_versions: List[dict] = [
        {"browser": "Chrome", "version": 88},
        {"browser": "Firefox", "version": 78},
        {"browser": "Edge", "version": 100},
    ]

    # 是否基于min_browser_versions开启严格的浏览器类型限制
    # 不在min_browser_versions规则内的浏览器将被直接拦截
    strict_browser_type_check: bool = False

    # 是否启用重复登录辅助检查
    enable_duplicate_login_check: bool = False

    # 重复登录辅助检查轮询间隔时间，单位：秒
    duplicate_login_check_interval: Union[int, float] = 10

    # 登录会话token对应的cookies项名称
    # 由于同一主机地址下的不同端口，在浏览器中会共享cookies
    # 因此在同一主机地址下部署多套基于magic-dash-pro模板开发的独立项目时
    # 请为各个项目设置不同的session_token_cookie_name
    session_token_cookie_name: str = "session_token"

    # 是否开启全屏额外水印功能
    enable_fullscreen_watermark: bool = False

    # 当开启了全屏额外水印功能时，用于动态处理实际水印内容输出
    fullscreen_watermark_generator: Callable = lambda current_user: (
        current_user.user_name
    )

    # 是否启用登录密码RSA加密传输功能
    # 开启后需配合HTTPS环境使用，否则浏览器端Web Crypto API在非安全上下文中可能不可用
    enable_login_rsa_crypto: bool = False

    # 用于登录密码加密传输的RSA公钥文件路径
    rsa_public_key_path: str = "magic_dash_pro_public_key.pem"

    # 用于登录密码加密传输的RSA私钥文件路径
    rsa_private_key_path: str = "magic_dash_pro_private_key.pem"

    # 针对用户登录页面，是否添加额外的滑块验证
    enable_login_captcha: bool = False
