from dash import html
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style

from configs import RouterConfig


def render(pathname: str):
    """子页面：独立通配页面渲染简单示例"""

    # 当前通配页面自定义信息提取规则

    # 当前页面通配规则
    pattern = RouterConfig.wildcard_patterns["独立通配页面演示"]

    # 通配内容提取结果
    wildcard_extract_result = pattern.findall(pathname)

    if wildcard_extract_result:
        match_content = wildcard_extract_result[0]
    else:
        match_content = None

    return html.Div(
        fac.AntdAlert(
            type="info",
            showIcon=True,
            message="这里是独立通配页面演示示例，当前通配匹配结果：{}".format(
                match_content or "无"
            ),
            description=fac.AntdText(
                [
                    "本页面模块路径：",
                    fac.AntdText(
                        "views/core_pages/independent_wildcard_page_demo.py",
                        strong=True,
                    ),
                ]
            ),
        ),
        style=style(padding="24px 32px"),
    )
