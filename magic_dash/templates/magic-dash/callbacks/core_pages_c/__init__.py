import time
import dash
from dash import Patch
import feffery_antd_components as fac
from dash.dependencies import Input, Output, State, ClientsideFunction

from server import app
from views.status_pages import _404
from views.core_pages import (
    index,
    page1,
    sub_menu_page1,
    sub_menu_page2,
    sub_menu_page3,
    independent_page,
    independent_wildcard_page,
    url_params_page,
)

# 路由配置参数
from configs import RouterConfig

app.clientside_callback(
    # 控制核心页面侧边栏折叠
    ClientsideFunction(
        namespace="clientside_basic", function_name="handleSideCollapse"
    ),
    [
        Output("core-side-menu-collapse-button-icon", "icon"),
        Output("core-header-side", "style"),
        Output("core-header-title", "style"),
        Output("core-side-menu-affix", "style"),
        Output("core-side-menu", "inlineCollapsed"),
    ],
    Input("core-side-menu-collapse-button", "nClicks"),
    [
        State("core-side-menu-collapse-button-icon", "icon"),
        State("core-header-side", "style"),
        State("core-page-config", "data"),
    ],
    prevent_initial_call=True,
)

app.clientside_callback(
    # 控制页首页面搜索切换功能
    ClientsideFunction(
        namespace="clientside_basic", function_name="handleCorePageSearch"
    ),
    Input("core-page-search", "value"),
)

app.clientside_callback(
    # 控制ctrl+k快捷键聚焦页面搜索框
    ClientsideFunction(
        namespace="clientside_basic", function_name="handleCorePageSearchFocus"
    ),
    # 其中更新key用于强制刷新状态
    [
        Output("core-page-search", "autoFocus"),
        Output("core-page-search", "key"),
    ],
    Input("core-ctrl-k-key-press", "pressedCounts"),
    prevent_initial_call=True,
)


@app.callback(
    [
        Output("core-container", "children"),
        Output("core-container", "items"),
        Output("core-container", "activeKey"),
        Output("core-side-menu", "currentKey"),
        Output("core-side-menu", "openKeys"),
        Output("core-silently-update-pathname", "pathname"),
    ],
    [
        Input("core-url", "pathname"),
        Input("core-container", "activeKey"),
    ],
    [
        State("core-container", "itemKeys"),
        State("core-page-config", "data"),
        State("core-side-menu", "inlineCollapsed"),
        State("core-url", "href"),
    ],
    running=[[Output("layout-top-progress", "spinning"), True, False]],
)
def core_router(
    pathname,
    tabs_active_key,
    tabs_item_keys,
    page_config,
    side_menu_inline_collapsed,
    current_url,
):
    """核心页面路由控制及侧边菜单同步"""

    # 统一首页pathname
    if pathname == RouterConfig.index_pathname:
        pathname = "/"

    # 若当前目标pathname不合法
    if pathname not in RouterConfig.valid_pathnames.keys():
        return _404.render(), pathname, dash.no_update

    # 仅单页面形式下为骨架屏动画添加额外效果持续时间
    if page_config["core_layout_type"] == "single":
        # 增加一点加载动画延迟^_^
        time.sleep(0.5)

    # 初始化页面返回内容
    page_content = fac.AntdAlert(
        type="warning",
        showIcon=True,
        message=f"这里是{pathname}",
        description="该页面尚未进行开发哦🤔~",
    )

    # 以首页做简单示例
    if pathname == "/":
        # 更新页面返回内容
        page_content = index.render()

    # 以主要页面1做简单示例
    elif pathname == "/core/page1":
        # 更新页面返回内容
        page_content = page1.render()

    # 以子菜单演示1做简单示例
    elif pathname == "/core/sub-menu-page1":
        # 更新页面返回内容
        page_content = sub_menu_page1.render()

    # 以子菜单演示2做简单示例
    elif pathname == "/core/sub-menu-page2":
        # 更新页面返回内容
        page_content = sub_menu_page2.render()

    # 以子菜单演示3做简单示例
    elif pathname == "/core/sub-menu-page3":
        # 更新页面返回内容
        page_content = sub_menu_page3.render()

    # 以独立页面做简单示例
    elif pathname == "/core/independent-page":
        # 更新页面返回内容
        page_content = independent_page.render()

    # 以独立通配页面做简单示例
    elif pathname == "/core/independent-wildcard-page":
        # 更新页面返回内容
        page_content = independent_wildcard_page.render()

    # 以url参数提取页面做简单示例
    elif pathname == "/core/url-params-page":
        # 更新页面返回内容
        page_content = url_params_page.render(current_url=current_url)

    ### ADD_PAGE 逻辑插入位置
    ### NEW_PAGE_TARGET

    # 多标签页形式
    if page_config.get("core_layout_type") == "tabs":
        # 基于Patch进行标签页子项远程映射更新
        p = Patch()

        tabs_item_keys = tabs_item_keys or []

        # 若标签页子项此前为空，即初始化加载
        if not tabs_item_keys:
            # 根据当前目标标签页，处理标签页子项的追加操作
            if pathname in ["/", RouterConfig.index_pathname]:
                p.append(
                    {
                        "label": "首页",
                        "key": "/",
                        "children": index.render(),
                        "closable": False,
                        "contextMenu": [
                            {"key": key, "label": key}
                            for key in ["关闭其他", "刷新页面"]
                        ],
                    }
                )
            else:
                p.extend(
                    [
                        {
                            "label": "首页",
                            "key": "/",
                            "children": index.render(),
                            "closable": False,
                            "contextMenu": [
                                {"key": key, "label": key}
                                for key in ["关闭其他", "刷新页面"]
                            ],
                        },
                        {
                            "label": RouterConfig.valid_pathnames[pathname],
                            "key": pathname,
                            "children": page_content,
                            "contextMenu": [
                                {"key": key, "label": key}
                                for key in [
                                    "关闭当前",
                                    "关闭其他",
                                    "关闭所有",
                                    "刷新页面",
                                ]
                            ],
                        },
                    ]
                )

            next_active_key = pathname
            next_current_key = pathname
            next_pathname = dash.no_update

        # 若标签页子项此前不为空，即用户手动切换标签页
        else:
            next_active_key = dash.no_update
            next_current_key = tabs_active_key
            next_pathname = tabs_active_key

            if dash.ctx.triggered_id == "core-url":
                if pathname not in tabs_item_keys:
                    p.append(
                        {
                            "label": RouterConfig.valid_pathnames[pathname],
                            "key": pathname,
                            "children": page_content,
                            "contextMenu": [
                                {"key": key, "label": key}
                                for key in [
                                    "关闭当前",
                                    "关闭其他",
                                    "关闭所有",
                                    "刷新页面",
                                ]
                            ],
                        }
                    )
                    next_active_key = pathname
                    next_current_key = pathname
                    next_pathname = dash.no_update
                else:
                    next_active_key = pathname
                    next_current_key = dash.no_update
                    next_pathname = dash.no_update

        return [
            # 当前模式下不操作children
            dash.no_update,
            p,
            next_active_key,
            next_current_key,
            (
                # 多标签模式下，侧边菜单折叠时不更新
                dash.no_update
                if side_menu_inline_collapsed
                else RouterConfig.side_menu_open_keys.get(pathname, dash.no_update)
            ),
            # 静默更新pathname
            next_pathname,
        ]

    # 单页面形式
    return [
        page_content,
        # 当前模式下不操作items
        dash.no_update,
        # 当前模式下不操作activeKey
        dash.no_update,
        pathname,
        RouterConfig.side_menu_open_keys.get(pathname, dash.no_update),
        # 当前模式下不操作pathname
        dash.no_update,
    ]


app.clientside_callback(
    ClientsideFunction(
        namespace="clientside_basic", function_name="handleCoreTabsClose"
    ),
    [
        Output("core-container", "items", allow_duplicate=True),
        Output("core-container", "activeKey", allow_duplicate=True),
    ],
    [
        Input("core-container", "tabCloseCounts"),
        Input("core-container", "clickedContextMenu"),
    ],
    [State("core-container", "latestDeletePane"), State("core-container", "items")],
    prevent_initial_call=True,
)

app.clientside_callback(
    ClientsideFunction(
        namespace="clientside_basic", function_name="handleCoreFullscreenToggle"
    ),
    [
        Output("core-fullscreen", "isFullscreen"),
        Output("core-full-screen-toggle-button-icon", "icon"),
    ],
    [
        Input("core-full-screen-toggle-button", "nClicks"),
        Input("core-fullscreen", "isFullscreen"),
    ],
    State("core-full-screen-toggle-button-icon", "icon"),
    prevent_initial_call=True,
)
