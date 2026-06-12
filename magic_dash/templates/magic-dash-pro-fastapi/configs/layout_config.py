from typing import Literal


class LayoutConfig:
    """页面布局相关配置参数"""

    # 核心页面侧边栏像素宽度
    core_side_width: int = 350

    # 登录页面内容区域渲染形式，可选项有'image'（图片内容）、'video'（视频内容）、'gradient'（渐变色背景）
    login_content_type: Literal["image", "video", "gradient"] = "gradient"

    # 登录页面布局形式，可选项有'content-left'（左侧内容右侧登录控件）、'form-left'（左侧登录控件右侧内容）、'centered'（居中登录控件，背景为内容）
    login_page_layout: Literal["content-left", "form-left", "centered"] = "centered"

    # 核心页面呈现类型，可选项有'single'（单页面形式）、'tabs'（多标签页形式）
    core_layout_type: Literal["single", "tabs"] = "single"

    # 是否在页首中显示页面搜索框
    show_core_page_search: bool = True
