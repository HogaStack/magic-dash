import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style


def render():
    """子页面：子菜单演示1渲染简单示例"""

    return fac.AntdSpace(
        [
            fac.AntdBreadcrumb(
                items=[
                    {"title": "主要页面"},
                    {"title": "子菜单演示"},
                    {
                        "title": "子菜单演示1",
                        "menuItems": [
                            {
                                "title": "子菜单演示2",
                                "href": "/core/sub-menu-page2",
                                "target": "_blank",
                            },
                            {
                                "title": "子菜单演示3",
                                "href": "/core/sub-menu-page3",
                                "target": "_blank",
                            },
                        ],
                    },
                ]
            ),
            fac.AntdAlert(
                type="info",
                showIcon=True,
                message="这里是子菜单演示1演示示例",
                description=fac.AntdText(
                    [
                        "本页面模块路径：",
                        fac.AntdText("views/core_pages/sub_menu_page1.py", strong=True),
                    ]
                ),
            ),
        ],
        direction="vertical",
        style=style(width="100%"),
    )
