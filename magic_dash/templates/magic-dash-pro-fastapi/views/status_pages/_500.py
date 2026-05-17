import traceback
from dash import html
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style


def render(e: str = None, e_detail: str = None):
    """渲染500状态页面"""

    # 提取错误详细信息
    e_detail = traceback.format_exc()

    return fac.AntdCenter(
        fac.AntdResult(
            # 自定义状态图片
            icon=html.Img(
                src="/assets/imgs/status/500.svg",
                style=style(height="50vh", pointerEvents="none"),
            ),
            title=fac.AntdText("系统内部错误", style=style(fontSize=20)),
            subTitle=fac.AntdButton(
                "返回首页", type="primary", href="/", target="_self"
            ),
            extra=fac.AntdAlert(
                description=fac.AntdText(
                    "具体错误信息：\n" + (e_detail if e else "500状态页演示示例错误"),
                    type="secondary",
                    style=style(
                        whiteSpace="pre-wrap",
                        wordBreak="break-all",
                    ),
                ),
                style=style(textAlign="left"),
            ),
        ),
        style={"minHeight": "calc(60vh + 100px)"},
    )
