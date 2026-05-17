from dash import html
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style


def render():
    """渲染403状态页面"""

    return fac.AntdCenter(
        fac.AntdResult(
            # 自定义状态图片
            icon=html.Img(
                src="/assets/imgs/status/403.svg",
                style=style(height="50vh", pointerEvents="none"),
            ),
            title=fac.AntdText("权限不足", style=style(fontSize=20)),
            subTitle="您没有访问该页面的权限",
            extra=fac.AntdButton("返回首页", type="primary", href="/", target="_self"),
        ),
        style={"height": "calc(60vh + 100px)"},
    )
