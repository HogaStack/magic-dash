from copy import deepcopy
import feffery_antd_components as fac
import feffery_utils_components as fuc
from feffery_dash_utils.style_utils import style
from feffery_dash_utils.tree_utils import TreeManager

# 路由配置参数
from configs import RouterConfig, LayoutConfig


def render(current_user_access_rule: str):
    """渲染核心功能页面侧边菜单栏

    Args:
        current_user_access_rule (str): 当前用户页面可访问性规则
    """

    current_menu_items = deepcopy(RouterConfig.core_side_menu)

    # 根据current_user_access_rule规则过滤菜单结构
    if current_user_access_rule["type"] == "include":
        for key in RouterConfig.valid_pathnames.keys():
            if key not in current_user_access_rule.get("keys", []):
                # 首页不受权限控制影响
                if key not in [
                    "/",
                    RouterConfig.index_pathname,
                ]:
                    current_menu_items = TreeManager.delete_node(
                        current_menu_items,
                        key,
                        data_type="menu",  # 菜单数据模式
                        keep_empty_children_node=False,  # 去除children字段为空列表的节点
                    )

    elif current_user_access_rule["type"] == "exclude":
        for key in RouterConfig.valid_pathnames.keys():
            if key in current_user_access_rule.get("keys", []):
                # 首页不受权限控制影响
                if key not in [
                    "/",
                    RouterConfig.index_pathname,
                ]:
                    current_menu_items = TreeManager.delete_node(
                        current_menu_items,
                        key,
                        data_type="menu",  # 菜单数据模式
                        keep_empty_children_node=False,  # 去除children字段为空列表的节点
                    )

    return fac.AntdAffix(
        fuc.FefferyDiv(
            [
                # 侧边菜单
                fac.AntdMenu(
                    id="core-side-menu",
                    menuItems=current_menu_items,
                    mode="inline",
                    style=style(border="none", width="100%"),
                )
            ],
            scrollbar="hidden",
            style=style(
                height="calc(100vh - 72px)",
                overflowY="auto",
                borderRight="1px solid #dae0ea",
                padding="0 8px",
            ),
        ),
        id="core-side-menu-affix",
        offsetTop=72.1,
        style=style(width=LayoutConfig.core_side_width),
    )
