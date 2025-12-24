import time
import dash
from dash import set_props, Patch
from dash.dependencies import Input, Output, State, ClientsideFunction

from server import app
from views.status_pages import _404
from components import page_content  # 页面内容渲染

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
    Input("core-pages-header-user-dropdown", "nClicks"),
    State("core-pages-header-user-dropdown", "clickedKey"),
)
def open_user_manage_drawer(nClicks, clickedKey):
    """打开个人信息、用户管理面板"""

    if clickedKey == "个人信息":
        set_props("personal-info-modal", {"visible": True, "loading": True})

    elif clickedKey == "用户管理":
        set_props("user-manage-drawer", {"visible": True, "loading": True})

    elif clickedKey == "部门管理":
        set_props("department-manage-drawer", {"visible": True, "loading": True})


@app.callback(
    [
        Output("core-container", "children"),
        Output("core-container", "items"),
        Output("core-container", "activeKey"),
        Output("core-side-menu", "currentKey"),
        Output("core-side-menu", "openKeys"),
        Output("core-silently-update-pathname", "pathname"),
    ],
    [Input("core-url", "pathname"), Input("core-container", "activeKey")],
    [
        State("core-container", "itemKeys"),
        State("core-container-tab-item-keys-cache", "data", allow_optional=True),
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
    tabs_item_keys_cache,
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
        return [
            _404.render(),
            pathname,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        ]

    # 仅单页面形式下为骨架屏动画添加额外效果持续时间
    if page_config["core_layout_type"] == "single":
        # 增加一点加载动画延迟^_^
        time.sleep(0.5)

    # 多标签页形式
    if page_config.get("core_layout_type") == "tabs":
        # 基于Patch进行标签页子项远程映射更新
        p = Patch()

        tabs_item_keys = tabs_item_keys or []

        # 若标签页子项此前为空，即初始化加载
        if not tabs_item_keys:
            # 处理session生命周期内，标签页key值缓存的还原
            tabs_item_keys = tabs_item_keys_cache or ["/"]
            # 处理新标签页追加
            if (
                pathname not in ["/", RouterConfig.index_pathname]
                and pathname not in tabs_item_keys
            ):
                tabs_item_keys.append(pathname)

            # 基于tabs_item_keys构造标签页子项
            for item_key in tabs_item_keys:
                if item_key == "/":
                    p.append(
                        {
                            "label": "首页",
                            "key": "/",
                            "children": page_content.render(
                                pathname="/", current_url=current_url
                            ),
                            "closable": False,
                            "contextMenu": [
                                {"key": key, "label": key}
                                for key in ["关闭其他", "刷新页面"]
                            ],
                        },
                    )
                else:
                    p.append(
                        {
                            "label": RouterConfig.valid_pathnames[item_key],
                            "key": item_key,
                            "children": page_content.render(
                                pathname=item_key, current_url=current_url
                            ),
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
                            "children": page_content.render(
                                pathname=pathname, current_url=current_url
                            ),
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
        page_content.render(pathname=pathname, current_url=current_url),
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
    """
(itemKeys) => {
    return itemKeys || [];
}
    """,
    Output("core-container-tab-item-keys-cache", "data"),
    Input("core-container", "itemKeys"),
)

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
