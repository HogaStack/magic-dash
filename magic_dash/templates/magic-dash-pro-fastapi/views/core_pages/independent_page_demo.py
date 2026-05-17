from dash import html
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style


def render():
    """子页面：独立页面渲染简单示例"""

    return html.Div(
        fac.AntdAlert(
            type="info",
            showIcon=True,
            message="这里是独立页面演示示例",
            description=fac.AntdText(
                [
                    "本页面模块路径：",
                    fac.AntdText(
                        "views/core_pages/independent_page_demo.py", strong=True
                    ),
                ]
            ),
        ),
        style=style(padding="24px 32px"),
    )
