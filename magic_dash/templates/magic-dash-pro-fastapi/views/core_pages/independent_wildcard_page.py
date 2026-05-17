from dash import html
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style


def render():
    """子页面：独立通配页面渲染入口页简单示例"""

    return fac.AntdSpace(
        [
            fac.AntdBreadcrumb(
                items=[{"title": "主要页面"}, {"title": "独立通配页面渲染入口页"}]
            ),
            fac.AntdAlert(
                type="info",
                showIcon=True,
                message="这里是独立通配页面渲染入口页演示示例",
                description=fac.AntdText(
                    [
                        "演示独立通配页面：",
                        html.A(
                            "通配演示1",
                            href="/core/independent-wildcard-page/demo/a",
                            target="_blank",
                        ),
                        "、",
                        html.A(
                            "通配演示2",
                            href="/core/independent-wildcard-page/demo/b",
                            target="_blank",
                        ),
                        "、",
                        html.A(
                            "通配演示3",
                            href="/core/independent-wildcard-page/demo/c",
                            target="_blank",
                        ),
                        html.Br(),
                        "本页面模块路径：",
                        fac.AntdText(
                            "views/core_pages/independent_wildcard_page.py", strong=True
                        ),
                    ]
                ),
            ),
        ],
        direction="vertical",
        style=style(width="100%"),
    )
