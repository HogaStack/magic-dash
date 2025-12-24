import uuid
import time
import dash
from dash import set_props
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style
from dash.dependencies import Input, Output, State

from server import app
from models.users import Users
from models.departments import Departments


def render():
    """渲染部门管理抽屉"""

    return fac.Fragment(
        [
            fac.AntdDrawer(
                id="department-manage-drawer",
                title=fac.AntdSpace([fac.AntdIcon(icon="antd-apartment"), "部门管理"]),
                width="65vw",
            ),
        ]
    )


def update_department_manage_drawer_content():
    """当前模块内复用工具函数，更新部门管理抽屉内容"""

    # 构建相关操作模态框
    modals = fac.Fragment(
        [
            # 新增部门模态框
            fac.AntdModal(
                id="department-manage-add-department-modal",
                title=fac.AntdSpace([fac.AntdIcon(icon="antd-apartment"), "新增部门"]),
                mask=False,
                renderFooter=True,
                okClickClose=False,
            ),
            # 删除部门模态框
            fac.AntdModal(
                id="department-manage-delete-department-modal",
                title=fac.AntdSpace([fac.AntdIcon(icon="antd-delete"), "删除部门"]),
                mask=False,
                renderFooter=True,
                okClickClose=False,
            ),
        ]
    )

    # 查询当前全部部门信息
    departments = Departments.get_all_departments()

    # 若当前无有效部门信息
    if not departments:
        return fac.Fragment(
            [
                # 构建相关操作模态框
                modals,
                fac.AntdAlert(
                    message="当前无有效部门信息",
                    description=fac.AntdButton(
                        "新增部门",
                        id="department-manage-add-department",
                        size="small",
                        type="primary",
                    ),
                    type="info",
                    showIcon=True,
                ),
            ]
        )

    return fac.Fragment(
        [
            # 构建相关操作模态框
            modals,
            fac.AntdSpace(
                [
                    fac.AntdButton(
                        "新增部门",
                        id="department-manage-add-department",
                        size="small",
                        type="primary",
                    ),
                    fac.AntdAlert(
                        message="操作提示：点击上方按钮创建新部门，右键下方有效部门节点进入部门删除等操作",
                        type="info",
                        showIcon=True,
                    ),
                    fac.AntdText(
                        "当前有效部门数量：{}".format(len(departments)),
                        type="secondary",
                    ),
                    fac.AntdDivider(style=style(marginTop=8, marginBottom=8)),
                    fac.AntdTree(
                        id="department-manage-tree",
                        key=str(uuid.uuid4()),  # 强制刷新
                        treeDataMode="flat",
                        treeData=[
                            {
                                "title": "全部部门",
                                "key": "[ALL_DEPARTMENTS]",
                            },
                            *[
                                {
                                    "title": item["department_name"],
                                    "key": item["department_id"],
                                    "parent": (
                                        item["parent_department_id"]
                                        or "[ALL_DEPARTMENTS]"
                                    ),
                                    "contextMenu": [
                                        {
                                            "key": "删除当前部门",
                                            "label": "删除当前部门",
                                        },
                                    ],
                                }
                                for item in departments
                            ],
                        ],
                        treeNodeKeyToTitle={
                            "[ALL_DEPARTMENTS]": fac.AntdSpace(
                                [fac.AntdIcon(icon="antd-home"), "全部部门"],
                                size=3,
                            )
                        },
                        defaultExpandAll=True,
                        selectable=False,
                        style=style(width="100%"),
                    ),
                ],
                direction="vertical",
                style=style(width="100%"),
            ),
        ]
    )


@app.callback(
    [
        Output("department-manage-drawer", "children"),
        Output("department-manage-drawer", "loading", allow_duplicate=True),
    ],
    Input("department-manage-drawer", "visible"),
    prevent_initial_call=True,
)
def render_department_manage_drawer(visible):
    """每次部门管理抽屉打开后，动态更新内容"""

    if visible:
        time.sleep(0.5)

        return update_department_manage_drawer_content(), False

    return dash.no_update


@app.callback(
    [
        Output("department-manage-add-department-modal", "visible"),
        Output("department-manage-add-department-modal", "children"),
    ],
    Input("department-manage-add-department", "nClicks"),
    prevent_initial_call=True,
)
def open_add_department_modal(nClicks):
    """打开新增部门模态框"""

    # 查询当前全部部门信息
    departments = Departments.get_all_departments()

    return [
        True,
        fac.AntdForm(
            [
                fac.AntdFormItem(
                    fac.AntdInput(
                        id="department-manage-add-department-form-department-name",
                        placeholder="请输入部门名称",
                        allowClear=True,
                    ),
                    label="部门名称",
                ),
                fac.AntdFormItem(
                    fac.AntdSelect(
                        id="department-manage-add-department-form-parent-department-id",
                        options=[
                            {
                                "label": item["department_name"],
                                "value": item["department_id"],
                            }
                            for item in departments
                        ],
                        allowClear=True,
                        placeholder="请选择，无上级部门时不选",
                    ),
                    label="上级部门",
                ),
            ],
            id="department-manage-add-department-form",
            key=str(uuid.uuid4()),  # 强制刷新
            enableBatchControl=True,
            layout="vertical",
            values={},
            style=style(marginTop=32),
        ),
    ]


@app.callback(
    Input("department-manage-add-department-modal", "okCounts"),
    [State("department-manage-add-department-form", "values")],
    prevent_initial_call=True,
)
def handle_add_department(okCounts, values):
    """处理新增部门逻辑"""

    # 获取表单数据
    values = values or {}

    # 检查表单数据完整性
    if not values.get("department-manage-add-department-form-department-name"):
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="请完善部门信息后再提交",
                )
            },
        )

    else:
        # 检查部门名称是否重复
        match_department = Departments.get_department_by_name(
            values["department-manage-add-department-form-department-name"]
        )

        # 若部门名称重复
        if match_department:
            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="error",
                        content="部门名称已存在",
                    )
                },
            )

        else:
            # 新增部门
            Departments.add_department(
                department_id=str(uuid.uuid4()),
                department_name=values[
                    "department-manage-add-department-form-department-name"
                ],
                parent_department_id=values.get(
                    "department-manage-add-department-form-parent-department-id"
                ),
            )

            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="success",
                        content="部门添加成功",
                    )
                },
            )

            # 刷新部门管理抽屉内容
            set_props(
                "department-manage-drawer",
                {"children": update_department_manage_drawer_content()},
            )


@app.callback(
    [
        Output("department-manage-delete-department-modal", "visible"),
        Output("department-manage-delete-department-modal", "children"),
    ],
    Input("department-manage-tree", "clickedContextMenu"),
    prevent_initial_call=True,
)
def open_delete_department_modal(clickedContextMenu):
    """打开删除部门模态框"""

    # 查询当前对应部门
    match_department = Departments.get_department(
        department_id=clickedContextMenu["nodeKey"]
    )

    # 查询当前对应部门内部员工信息
    match_users = Users.get_users_by_department_id(
        department_id=clickedContextMenu["nodeKey"]
    )

    # 查询当前部门下一级所有部门信息
    match_children_departments = Departments.get_children_departments(
        department_id=clickedContextMenu["nodeKey"]
    )

    return [
        True,
        fac.AntdAlert(
            type="warning",
            showIcon=True,
            message=fac.AntdText(
                [
                    "确定要删除部门【",
                    fac.AntdText(
                        match_department.department_name,
                        strong=True,
                        style=style(fontSize=16),
                    ),
                    "】吗？",
                ],
                style=style(fontSize=16),
            ),
            description=fac.AntdSpace(
                [
                    "该部门涉及用户数量：{}".format(len(match_users)),
                    "该部门下属一级部门数量：{}".format(
                        len(match_children_departments)
                    ),
                ],
                direction="vertical",
                size=0,
                style=style(width="100%"),
            ),
            style=style(marginTop=24, marginBottom=24),
        ),
    ]


@app.callback(
    Input("department-manage-delete-department-modal", "okCounts"),
    [State("department-manage-tree", "clickedContextMenu")],
    prevent_initial_call=True,
)
def handle_delete_department(okCounts, clickedContextMenu):
    """处理删除部门逻辑"""

    # 删除部门
    Departments.delete_department(department_id=clickedContextMenu["nodeKey"])

    set_props(
        "global-message",
        {
            "children": fac.AntdMessage(
                type="success",
                content="部门删除成功",
            )
        },
    )

    # 刷新部门管理抽屉内容
    set_props(
        "department-manage-drawer",
        {"children": update_department_manage_drawer_content()},
    )
