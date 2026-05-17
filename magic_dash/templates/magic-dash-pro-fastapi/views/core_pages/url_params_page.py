import json
from yarl import URL
from dash import html
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style


def render(current_url: str):
    """子页面：url参数提取简单示例

    Args:
        current_url (str): 当前url
    """

    # 以yarl为例，解析当前url中的各部分信息
    parsed_url = URL(current_url)

    return fac.AntdSpace(
        [
            fac.AntdBreadcrumb(items=[{"title": "主要页面"}, {"title": "url参数提取"}]),
            fac.AntdAlert(
                type="info",
                showIcon=True,
                message="这里是url参数提取演示示例",
                description=fac.AntdText(
                    [
                        "本页面模块路径：",
                        fac.AntdText(
                            "views/core_pages/url_params_page.py", strong=True
                        ),
                    ]
                ),
            ),
            fac.AntdText("演示链接："),
            fac.AntdSpace(
                [
                    html.A(
                        url,
                        href=url,
                        target="_blank",
                    )
                    for url in [
                        "/core/url-params-page",
                        "/core/url-params-page?a=1&b=2",
                        "/core/url-params-page?a=1&b=2&c=3&c=4",
                    ]
                ],
                direction="vertical",
                size="small",
                style=style(width="100%"),
            ),
            fac.AntdText("当前页面渲染来源URL信息："),
            fac.AntdDescriptions(
                items=[
                    {
                        "label": "scheme",
                        "children": parsed_url.scheme,
                    },
                    {
                        "label": "host",
                        "children": parsed_url.host,
                    },
                    {
                        "label": "path",
                        "children": parsed_url.path,
                    },
                    {
                        "label": "port",
                        "children": parsed_url.port,
                    },
                    {
                        "label": "query",
                        "children": json.dumps(
                            {
                                key: parsed_url.query.getall(key)
                                for key in parsed_url.query.keys()
                            }
                        ),
                    },
                ],
                bordered=True,
                size="small",
            ),
        ],
        direction="vertical",
        style=style(width="100%"),
    )
