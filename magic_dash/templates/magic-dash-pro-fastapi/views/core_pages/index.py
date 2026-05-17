from dash import html
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style


def render():
    """子页面：首页渲染简单示例"""

    return fac.AntdSpace(
        [
            fac.AntdBreadcrumb(items=[{"title": "主要页面"}, {"title": "首页"}]),
            fac.AntdAlert(
                type="info",
                showIcon=True,
                message="欢迎来到首页！",
                description=fac.AntdText(
                    [
                        "这里以首页为例，演示核心页面下，各子页面构建方式的简单示例😉~",
                        html.Br(),
                        "本页面模块路径：",
                        fac.AntdText("views/core_pages/index.py", strong=True),
                    ]
                ),
            ),
        ],
        direction="vertical",
        style=style(width="100%"),
    )
