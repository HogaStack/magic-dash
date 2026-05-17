import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style


def render():
    """子页面：子菜单演示3渲染简单示例"""

    return fac.AntdSpace(
        [
            fac.AntdBreadcrumb(
                items=[
                    {"title": "主要页面"},
                    {"title": "子菜单演示"},
                    {
                        "title": "子菜单演示3",
                        "menuItems": [
                            {
                                "title": "子菜单演示1",
                                "href": "/core/sub-menu-page1",
                                "target": "_blank",
                            },
                            {
                                "title": "子菜单演示2",
                                "href": "/core/sub-menu-page2",
                                "target": "_blank",
                            },
                        ],
                    },
                ]
            ),
            fac.AntdAlert(
                type="info",
                showIcon=True,
                message="这里是子菜单演示3演示示例",
                description=fac.AntdText(
                    [
                        "本页面模块路径：",
                        fac.AntdText("views/core_pages/sub_menu_page3.py", strong=True),
                    ]
                ),
            ),
        ],
        direction="vertical",
        style=style(width="100%"),
    )
