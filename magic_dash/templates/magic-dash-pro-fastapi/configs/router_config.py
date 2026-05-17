import re
from typing import List, Union


class RouterConfig:
    """路由配置参数"""

    # 与应用首页对应的pathname地址
    index_pathname: str = "/index"

    # 核心页面侧边菜单完整结构
    core_side_menu: List[dict] = [
        {
            "component": "ItemGroup",
            "props": {
                "title": "主要页面",
                "key": "主要页面",
            },
            "children": [
                {
                    "component": "Item",
                    "props": {
                        "title": "首页",
                        "key": "/",
                        "icon": "antd-home",
                        "href": "/",
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "title": "主要页面1",
                        "key": "/core/page1",
                        "icon": "antd-app-store",
                        "href": "/core/page1",
                    },
                },
                {
                    "component": "SubMenu",
                    "props": {
                        "key": "子菜单演示",
                        "title": "子菜单演示",
                        "icon": "antd-catalog",
                    },
                    "children": [
                        {
                            "component": "Item",
                            "props": {
                                "key": "/core/sub-menu-page1",
                                "title": "子菜单演示1",
                                "href": "/core/sub-menu-page1",
                            },
                        },
                        {
                            "component": "Item",
                            "props": {
                                "key": "/core/sub-menu-page2",
                                "title": "子菜单演示2",
                                "href": "/core/sub-menu-page2",
                            },
                        },
                        {
                            "component": "Item",
                            "props": {
                                "key": "/core/sub-menu-page3",
                                "title": "子菜单演示3",
                                "href": "/core/sub-menu-page3",
                            },
                        },
                    ],
                },
                {
                    "component": "Item",
                    "props": {
                        "title": "独立页面渲染入口页",
                        "key": "/core/independent-page",
                        "icon": "antd-app-store",
                        "href": "/core/independent-page",
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "title": "独立通配页面渲染入口页",
                        "key": "/core/independent-wildcard-page",
                        "icon": "antd-app-store",
                        "href": "/core/independent-wildcard-page",
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "title": "url参数提取示例",
                        "key": "/core/url-params-page",
                        "icon": "antd-link",
                        "href": "/core/url-params-page",
                    },
                },
            ],
        },
        {
            "component": "ItemGroup",
            "props": {
                "title": "系统管理",
                "key": "系统管理",
            },
            "children": [
                {
                    "component": "SubMenu",
                    "props": {
                        "key": "日志管理",
                        "title": "日志管理",
                        "icon": "antd-history",
                    },
                    "children": [
                        {
                            "component": "Item",
                            "props": {
                                "key": "/core/login-logs",
                                "title": "登录日志",
                                "icon": "antd-login",
                                "href": "/core/login-logs",
                            },
                        },
                    ],
                },
            ],
        },
        {
            "component": "ItemGroup",
            "props": {
                "title": "其他页面",
                "key": "其他页面",
            },
            "children": [
                {
                    "component": "Item",
                    "props": {
                        "title": "其他页面1",
                        "key": "/core/other-page1",
                        "icon": "antd-app-store",
                        "href": "/core/other-page1",
                    },
                }
            ],
        },
    ]

    # 通配页面模式字典
    wildcard_patterns: dict = {
        "独立通配页面演示": re.compile(r"^/core/independent-wildcard-page/demo/(.*?)$")
    }

    # 有效页面pathname地址 -> 页面标题映射字典
    valid_pathnames: dict = {
        "/login": "登录页",
        "/": "首页",
        index_pathname: "首页",
        "/core/page1": "主要页面1",
        "/core/sub-menu-page1": "子菜单演示1",
        "/core/sub-menu-page2": "子菜单演示2",
        "/core/sub-menu-page3": "子菜单演示3",
        "/core/independent-page": "独立页面渲染入口页",
        "/core/independent-wildcard-page": "独立通配页面渲染入口页",
        "/core/url-params-page": "url参数提取示例",
        "/core/login-logs": "登录日志",
        "/core/other-page1": "其他页面1",
        "/403-demo": "403状态页演示",
        "/404-demo": "404状态页演示",
        "/500-demo": "500状态页演示",
        # 独立渲染页面
        "/core/independent-page/demo": "独立页面演示示例",
        # 独立通配渲染页面
        wildcard_patterns["独立通配页面演示"]: "独立通配页面演示示例",
    }

    # 独立渲染展示的核心页面
    independent_core_pathnames: List[Union[str, re.Pattern]] = [
        "/core/independent-page/demo",
        wildcard_patterns["独立通配页面演示"],
    ]

    # 无需权限校验的公开页面
    public_pathnames: List[str] = [
        "/login",
        "/logout",
        "/403-demo",
        "/404-demo",
        "/500-demo",
    ]

    # 部分页面pathname对应要展开的子菜单层级
    side_menu_open_keys: dict = {
        "/core/sub-menu-page1": ["子菜单演示"],
        "/core/sub-menu-page2": ["子菜单演示"],
        "/core/sub-menu-page3": ["子菜单演示"],
        "/core/login-logs": ["日志管理"],
    }
