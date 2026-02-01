import re
import dash
from dash import html, set_props
import feffery_antd_components as fac
import feffery_utils_components as fuc
from dash.dependencies import Input, Output, State
from feffery_dash_utils.version_utils import (
    check_python_version,
    check_dependencies_version,
)

from server import app
from configs import RouterConfig  # 路由配置参数
from views.status_pages import _404, _500  # 各状态页面
from views import core_pages

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
        # 全局页面刷新
        fuc.FefferyReload(id="global-reload"),
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

    # 演示专用页面展示
    if pathname == "/404-demo":
        return _404.render()
    if pathname == "/500-demo":
        return _500.render()

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
        # 处理核心功能页面渲染
        return core_pages.render(current_pathname=pathname)

    # 返回404状态页面
    return _404.render()


if __name__ == "__main__":
    # 非正式环境下开发调试预览用
    # 生产环境推荐使用gunicorn启动
    app.run(debug=True)
