import os
import sys
import importlib
import argparse

# 默认配置
core_pages_c_path = "./callbacks/core_pages_c/__init__.py"
router_config_path = "./configs/router_config.py"
core_pages_folder = "./views/core_pages"


# 添加core_pages_c
def page_import_adder(
    page_name,
    page_describe,
    page_url,
    core_pages_callbacks_path=core_pages_c_path,
    target_import="views.core_pages",
):
    """
    添加单个页面到 callbacks.py 文件的 views.core_pages 导入语句中，
    同时将页面路由逻辑添加到 core_router 函数的 ### NEW_PAGE_TARGET 注释之后。

    :param page_name: 页面名称
    :param page_describe: 页面描述/注释
    :param page_url: 页面的 URL 路径
    :param core_pages_callbacks_path: callbacks.py 文件路径，默认为指定路径
    :param target_import: 目标导入模块，默认为 "views.core_pages"
    """
    # 检查文件是否存在
    if not os.path.exists(core_pages_callbacks_path):
        raise FileNotFoundError(f"文件 {core_pages_callbacks_path} 不存在")

    # 读取 callbacks.py 文件内容
    with open(core_pages_callbacks_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 添加新的导入语句部分
    import_line_index = None
    for i, line in enumerate(lines):
        if f"from {target_import} import (" in line:
            import_line_index = i
            break

    if import_line_index is not None:
        import_end_index = import_line_index
        while import_end_index < len(lines) and ")" not in lines[import_end_index]:
            import_end_index += 1

        page_exists = any(
            page_name in line for line in lines[import_line_index : import_end_index + 1]
        )
        if not page_exists:
            new_line = f"    {page_name},  # {page_describe}\n"
            lines.insert(import_end_index, new_line)
            with open(core_pages_callbacks_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"成功添加 {page_name} 引用到 {core_pages_callbacks_path} {target_import}")
        else:
            print(f"{page_name} 引用已存在于 {core_pages_callbacks_path} {target_import}中")
    else:
        new_import = [
            f"from {target_import} import (\n",
            f"    {page_name},  # {page_describe}\n",
            ")\n",
        ]
        lines = new_import + lines
        with open(core_pages_callbacks_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"未找到导入语句，已添加新的导入语句并添加页面 {page_name}")

    # 生成新的路由逻辑代码
    new_code = [
        f"    # {page_describe}\n",
        f'    elif pathname == "{page_url}":\n',
        f"        page_content = {page_name}.render()\n",
    ]

    # 找到 ### NEW_PAGE_TARGET 注释位置并插入新代码
    for i, line in enumerate(lines):
        if "### NEW_PAGE_TARGET" in line:
            lines.insert(i + 1, "".join(new_code))
            with open(core_pages_callbacks_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"成功添加 {page_name} 路由逻辑至 core_router() ### NEW_PAGE_TARGET")
            break
    else:
        print("未找到 ### NEW_PAGE_TARGET 注释")


# 添加router配置
def page_router_adder(
    page_name,
    page_title,
    page_url,
    page_icon,
    page_describe,
    RouterConfigPath=router_config_path,
):
    """
    将page_router添加到RouterConfig.core_side_menu/valid_pathnames

    :param page_name: 页面名称
    :param page_title: 页面标题
    :param page_url: 页面路径
    :param page_describe: 页面描述
    :param RouterConfigPath: router_config.py 文件的路径
    """

    # 创建page_dict
    page_dict = {
        "component": "Item",
        "props": {
            "title": f"{page_title}",
            "key": f"/core/{page_name}",
            "icon": f"{page_icon}",
            "href": f"{page_url}",
        },
    }

    # 获取 router_config.py 文件目录
    router_config_dir = os.path.dirname(os.path.abspath(RouterConfigPath))
    router_config_file = os.path.basename(RouterConfigPath)
    router_config_module = router_config_file.replace(".py", "")

    # 将目录添加到 sys.path 导入
    if router_config_dir not in sys.path:
        sys.path.insert(0, router_config_dir)

    # 动态导入 RouterConfig
    router_config = importlib.import_module(router_config_module)

    # 将 page_dict 添加到 RouterConfig.core_side_menu
    router_config.RouterConfig.core_side_menu.append(page_dict)

    # 将页面信息添加到 RouterConfig.valid_pathnames
    if page_url and page_title:
        router_config.RouterConfig.valid_pathnames[page_url] = page_title  # page_describe

    # 读取原文件内容
    with open(RouterConfigPath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 找到 core_side_menu 的开始结束位置
    start_index = None
    end_index = None
    bracket_count = 0
    for i, line in enumerate(lines):
        if "core_side_menu:" in line:
            start_index = i
        if start_index is not None:
            bracket_count += line.count("[") - line.count("]")
            if bracket_count == 0:
                end_index = i
                break

    # 更新core_side_menu
    if start_index is not None and end_index is not None:
        # 找到core_side_menu的最后一个元素的结束位置
        last_bracket_index = None
        for i in range(end_index, start_index, -1):
            if "]" in lines[i]:
                last_bracket_index = i
                break

        # 在最后一个元素后添加新的页面字典
        if last_bracket_index is not None:
            if not lines[last_bracket_index - 1].strip().endswith(","):
                lines[last_bracket_index - 1] = lines[last_bracket_index - 1].rstrip() + ",\n"

            # 添加新的页面字典
            new_page_str = "        " + str(page_dict) + "\n    ]\n"
            lines[last_bracket_index] = new_page_str

    # 找到 valid_pathnames 的开始和结束位置
    start_index = None
    end_index = None
    bracket_count = 0
    for i, line in enumerate(lines):
        if "valid_pathnames:" in line:
            start_index = i
        if start_index is not None:
            bracket_count += line.count("{") - line.count("}")
            if bracket_count == 0:
                end_index = i
                break

    if start_index is not None and end_index is not None:
        last_bracket_index = None
        for i in range(end_index, start_index, -1):
            if "}" in lines[i]:
                last_bracket_index = i
                break

        # 在最后一个元素前添加新的页面信息
        if last_bracket_index is not None:
            # 添加新的页面信息
            new_page_str = f'        "{page_url}": "{page_title}",  # {page_describe}\n'
            lines.insert(last_bracket_index, new_page_str)

    # 将修改后的内容写回文件
    with open(RouterConfigPath, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(
        f"成功添加 {page_name} 页面路由配置至 {RouterConfigPath} 的 RouterConfig.core_side_menu/.valid_pathnames"
    )


# 生成pagefile
def page_file_generator(page_name, page_title, page_describe, output_folder=core_pages_folder):

    page_file_path = f"{output_folder}/{page_name}.py"

    # 默认py文件模板
    template = f"""
from dash import html
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style

def render():
    #"子页面：首页渲染简单示例

    return fac.AntdSpace(
        [
            fac.AntdBreadcrumb(items=[{{"title": "新页面"}}, {{"title": "{page_title}"}}]),
            fac.AntdAlert(
                type="info",
                showIcon=True,
                message="{page_name}",
                description=fac.AntdText(
                    [
                        "{page_describe}",
                        html.Br(),
                        "本页面模块路径：",
                        fac.AntdText("{page_file_path}", strong=True),
                    ]
                ),
            ),
        ],
        direction="vertical",
        style=style(width="100%"),
    )
"""

    output_pyfile_path = os.path.join(output_folder, page_name) + ".py"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    with open(f"{output_pyfile_path}", "w", encoding="utf-8") as f:
        f.write(template)
    print(f"成功新建 {page_name} 页面文件至 {output_pyfile_path}")


## main
def page_adder(
    page_name, page_title=None, page_describe=None, page_url=None, page_icon="antd-menu"
):
    # 当参数未输入时，从page_name自动生成
    if page_title is None:
        page_title = page_name

    if page_describe is None:
        page_describe = f"这是由ADD_PAGE自动生成的 {page_name} 页面的描述"

    if page_url is None:
        page_url = f"/core/{page_name}"

    page_import_adder(page_name=page_name, page_describe=page_describe, page_url=page_url)
    page_router_adder(
        page_name=page_name,
        page_title=page_title,
        page_url=page_url,
        page_describe=page_describe,
        page_icon=page_icon,
    )
    page_file_generator(
        page_name=page_name,
        page_title=page_title,
        page_describe=page_describe,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="添加新页面")
    parser.add_argument("--name", required=True, help="页面名称")
    parser.add_argument("--title", help="页面标题")
    parser.add_argument("--describe", help="页面描述")
    parser.add_argument("--url", help="页面URL")
    parser.add_argument("--icon", default="antd-menu", help="页面图标")

    args = parser.parse_args()

    page_adder(
        page_name=args.name,
        page_title=args.title,
        page_describe=args.describe,
        page_url=args.url,
        page_icon=args.icon,
    )
