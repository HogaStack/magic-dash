import feffery_antd_components as fac

from views.core_pages import (
    index,
    page1,
    sub_menu_page1,
    sub_menu_page2,
    sub_menu_page3,
    independent_page,
    independent_wildcard_page,
    url_params_page,
    # 系统管理相关页面
    login_logs,
)


def render(pathname: str, current_url: str = None):
    """渲染pathname对应的页面内容"""

    # 初始化页面返回内容
    page_content = fac.AntdAlert(
        type="warning",
        showIcon=True,
        message=f"这里是{pathname}",
        description="该页面尚未进行开发哦🤔~",
    )

    # 以首页做简单示例
    if pathname == "/":
        # 更新页面返回内容
        page_content = index.render()

    # 以主要页面1做简单示例
    elif pathname == "/core/page1":
        # 更新页面返回内容
        page_content = page1.render()

    # 以子菜单演示1做简单示例
    elif pathname == "/core/sub-menu-page1":
        # 更新页面返回内容
        page_content = sub_menu_page1.render()

    # 以子菜单演示2做简单示例
    elif pathname == "/core/sub-menu-page2":
        # 更新页面返回内容
        page_content = sub_menu_page2.render()

    # 以子菜单演示3做简单示例
    elif pathname == "/core/sub-menu-page3":
        # 更新页面返回内容
        page_content = sub_menu_page3.render()

    # 以独立页面做简单示例
    elif pathname == "/core/independent-page":
        # 更新页面返回内容
        page_content = independent_page.render()

    # 以独立通配页面做简单示例
    elif pathname == "/core/independent-wildcard-page":
        # 更新页面返回内容
        page_content = independent_wildcard_page.render()

    # 以url参数提取页面做简单示例
    elif pathname == "/core/url-params-page":
        # 更新页面返回内容
        page_content = url_params_page.render(current_url=current_url)

    # 系统管理相关页面
    # 日志管理-登录日志
    elif pathname == "/core/login-logs":
        # 更新页面返回内容
        page_content = login_logs.render()

    return page_content
