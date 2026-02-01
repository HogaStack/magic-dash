import re
import dash
from flask import request
from dash import html, set_props, dcc
import feffery_antd_components as fac
import feffery_utils_components as fuc
from dash.dependencies import Input, Output, State
from flask_principal import identity_changed, AnonymousIdentity
from flask_login import current_user, logout_user, AnonymousUserMixin
from feffery_dash_utils.version_utils import (
    check_python_version,
    check_dependencies_version,
)

from server import app
from models.users import Users
from views import core_pages, login
from views.status_pages import _403, _404, _500
from configs import BaseConfig, RouterConfig, AuthConfig

# 检查Python版本
check_python_version(min_version="3.8", max_version="3.13")
# 检查关键依赖库版本
check_dependencies_version(
    requirements_file="./requirements.txt",
)

app.layout = lambda: fuc.FefferyTopProgress(
    [
        # 全局消息提示
        fac.Fragment(id="global-message"),
        # 全局重定向
        fac.Fragment(id="global-redirect"),
        # 全局页面刷新
        fuc.FefferyReload(id="global-reload"),
        # 全局文件下载
        dcc.Download(id="global-download"),
        *(
            [
                # 重复登录辅助检查轮询
                dcc.Interval(
                    id="duplicate-login-check-interval",
                    interval=BaseConfig.duplicate_login_check_interval * 1000,
                )
            ]
            # 若开启了重复登录辅助检查
            if BaseConfig.enable_duplicate_login_check
            else []
        ),
        # 根节点url监听
        fuc.FefferyLocation(id="root-url"),
        # 应用根容器
        html.Div(
            id="root-container",
        ),
    ],
    id="layout-top-progress",
    minimum=0.33,
    color="#1677ff",
    manual=True,
)


def handle_root_router_error(e):
    """处理根节点路由错误"""

    set_props(
        "root-container",
        {
            "children": _500.render(e),
        },
    )


@app.callback(
    Output("root-container", "children"),
    Input("root-url", "pathname"),
    State("root-url", "trigger"),
    prevent_initial_call=True,
    on_error=handle_root_router_error,
    running=[[Output("layout-top-progress", "spinning"), True, False]],
)
def root_router(pathname, trigger):
    """根节点路由控制"""

    # 在动态路由切换时阻止根节点路由更新
    if trigger != "load":
        return dash.no_update

    # 无需校验登录状态的公共页面
    if pathname in RouterConfig.public_pathnames:
        if pathname == "/403-demo":
            return _403.render()

        elif pathname == "/404-demo":
            return _404.render()

        elif pathname == "/500-demo":
            return _500.render()

        elif pathname == "/login":
            return login.render()

        elif pathname == "/logout":
            # 当前用户登出
            logout_user()

            # 重置当前用户身份
            identity_changed.send(
                app.server,
                identity=AnonymousIdentity(),
            )

            # 重定向至登录页面
            set_props(
                "global-redirect",
                {
                    "children": dcc.Location(
                        pathname="/login", id="global-redirect-target"
                    )
                },
            )
            return dash.no_update

    # 登录状态校验：若当前用户未登录
    if not current_user.is_authenticated:
        # 重定向至登录页面
        set_props(
            "global-redirect",
            {"children": dcc.Location(pathname="/login", id="global-redirect-target")},
        )

        return dash.no_update

    # 检查当前访问目标pathname是否为有效页面
    if (
        # 硬编码页面地址
        pathname in RouterConfig.valid_pathnames.keys()
        or
        # 通配模式页面地址
        any(
            pattern.match(pathname)
            for pattern in RouterConfig.valid_pathnames.keys()
            if isinstance(pattern, re.Pattern)
        )
    ):
        # 校验当前用户是否具有针对当前访问目标页面的权限
        current_user_access_rule = AuthConfig.pathname_access_rules.get(
            current_user.user_role
        )

        # 检查是否满足通配渲染页面规则
        match_wildcard_patterns = [
            pattern
            for pattern in current_user_access_rule.get("keys", [])
            if isinstance(pattern, re.Pattern) and pattern.match(pathname)
        ]

        # 若当前用户页面权限规则类型为'include'
        if current_user_access_rule["type"] == "include":
            # 若当前用户不具有针对当前访问目标页面的权限
            if (
                pathname not in current_user_access_rule.get("keys", [])
                and not match_wildcard_patterns
            ):
                # 首页不受权限控制影响
                if pathname not in [
                    "/",
                    RouterConfig.index_pathname,
                ]:
                    # 重定向至403页面
                    set_props(
                        "global-redirect",
                        {
                            "children": dcc.Location(
                                pathname="/403-demo", id="global-redirect-target"
                            )
                        },
                    )

                    return dash.no_update

        # 若当前用户页面权限规则类型为'exclude'
        elif current_user_access_rule["type"] == "exclude":
            # 若当前用户不具有针对当前访问目标页面的权限
            if (
                pathname in current_user_access_rule.get("keys", [])
                or match_wildcard_patterns
            ):
                # 重定向至403页面
                set_props(
                    "global-redirect",
                    {
                        "children": dcc.Location(
                            pathname="/403-demo", id="global-redirect-target"
                        )
                    },
                )

                return dash.no_update

        # 处理核心功能页面渲染
        # 返回带水印的页面内容
        if BaseConfig.enable_fullscreen_watermark:
            return fac.AntdWatermark(
                core_pages.render(
                    current_user_access_rule=current_user_access_rule,
                    current_pathname=pathname,
                ),
                # 处理水印内容生成
                content=BaseConfig.fullscreen_watermark_generator(current_user),
            )

        # 返回不带水印的页面内容
        return core_pages.render(
            current_user_access_rule=current_user_access_rule, current_pathname=pathname
        )

    # 返回404状态页面
    return _404.render()


@app.callback(
    Input("duplicate-login-check-interval", "n_intervals"),
    State("root-url", "pathname"),
)
def duplicate_login_check(n_intervals, pathname):
    """重复登录辅助轮询检查"""

    # 若当前页面属于无需校验登录状态的公共页面，结束检查
    if pathname in RouterConfig.public_pathnames:
        return

    # 若当前用户身份未知
    if isinstance(current_user, AnonymousUserMixin):
        # 重定向到登出页
        set_props(
            "global-redirect",
            {"children": dcc.Location(pathname="/logout", id="global-redirect-target")},
        )

    # 若当前用户已登录
    elif current_user.is_authenticated:
        match_user = Users.get_user(current_user.id)
        # 若当前回调请求携带cookies中的session_token，当前用户数据库中的最新session_token不一致
        if match_user.session_token != request.cookies.get(
            BaseConfig.session_token_cookie_name
        ):
            # 重定向到登出页
            set_props(
                "global-redirect",
                {
                    "children": dcc.Location(
                        pathname="/logout", id="global-redirect-target"
                    )
                },
            )


if __name__ == "__main__":
    # 非正式环境下开发调试预览用
    # 生产环境推荐使用gunicorn启动
    app.run(debug=True)
