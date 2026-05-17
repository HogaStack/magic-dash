from dash import html
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style

# 令对应当前页面的回调函数子模块生效
import callbacks.core_pages_c.page1_c  # noqa: F401


def render():
    """子页面：主要页面1渲染简单示例"""

    return fac.AntdSpace(
        [
            fac.AntdBreadcrumb(items=[{"title": "主要页面"}, {"title": "主要页面1"}]),
            fac.AntdAlert(
                type="info",
                showIcon=True,
                message="这里是主要页面1演示示例",
                description=fac.AntdText(
                    [
                        "本页面简单演示了如何在当前项目模板中添加新的自定义页面，且页面内容中包含由回调函数控制的简单演示用交互功能。",
                        html.Br(),
                        "本页面模块路径：",
                        fac.AntdText("views/core_pages/page1.py", strong=True),
                        html.Br(),
                        "本页面回调模块路径：",
                        fac.AntdText("callbacks/core_pages_c/page1_c.py", strong=True),
                    ]
                ),
            ),
            fac.AntdText("回调功能演示："),
            fac.AntdSpace(
                [
                    fac.AntdButton(
                        "点击测试", id="core-page1-demo-button", type="primary"
                    ),
                    fac.AntdText("累计点击次数：0", id="core-page1-demo-output"),
                ]
            ),
        ],
        direction="vertical",
        style=style(width="100%"),
    )
