import dash
from dash import set_props
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style
from dash.dependencies import Input, Output, State
from werkzeug.security import generate_password_hash

from server import app
from models.users import Users
from configs import AuthConfig

import uuid
import time
import secrets
import string


def render():
    """渲染用户管理抽屉"""

    return fac.AntdDrawer(
        id="user-manage-drawer",
        title=fac.AntdSpace([fac.AntdIcon(icon="antd-team"), "用户管理"]),
        width="65vw",
    )


def refresh_user_manage_table_data():
    """当前模块内复用工具函数，刷新用户管理表格数据"""

    # 查询全部用户信息
    all_users = Users.get_all_users()

    return [
        {
            "user_id": item["user_id"],
            "user_name": item["user_name"],
            "user_role": {
                "tag": AuthConfig.roles.get(item["user_role"])["description"],
                "color": (
                    "gold" if item["user_role"] == AuthConfig.admin_role else "blue"
                ),
            },
            "操作": [
                {
                    "content": "删除",
                    "type": "link",
                    "danger": True,
                    "disabled": item["user_role"] == AuthConfig.admin_role,
                },
                {
                    "content": "重置密码",
                    "type": "link",
                    "danger": False,
                    "disabled": item["user_role"] == AuthConfig.admin_role,
                },
            ],
        }
        for item in all_users
    ]


@app.callback(
    [
        Output("user-manage-drawer", "children"),
        Output("user-manage-drawer", "loading", allow_duplicate=True),
    ],
    Input("user-manage-drawer", "visible"),
    prevent_initial_call=True,
)
def render_user_manage_drawer(visible):
    """每次用户管理抽屉打开后，动态更新内容"""

    if visible:
        time.sleep(0.5)

        return [
            [
                # 新增用户模态框
                fac.AntdModal(
                    id="user-manage-add-user-modal",
                    title=fac.AntdSpace(
                        [fac.AntdIcon(icon="antd-user-add"), "新增用户"]
                    ),
                    mask=False,
                    renderFooter=True,
                    okClickClose=False,
                ),
                # 删除用户模态框
                fac.AntdModal(
                    id="user-manage-delete-user-modal",
                    title=fac.AntdSpace(
                        [fac.AntdIcon(icon="antd-user-delete"), "删除用户"]
                    ),
                    mask=False,
                    renderFooter=True,
                    okClickClose=False,
                    visible=False,
                ),
                fac.AntdModal(
                    id="user-manage-reset-password-modal",
                    title=fac.AntdSpace(
                        [fac.AntdIcon(icon="antd-key"), "重置密码"]),
                    mask=False,
                    renderFooter=True,
                    okClickClose=False,
                    visible=False,
                ),
                fac.AntdSpace(
                    [
                        fac.AntdTable(
                            id="user-manage-table",
                            columns=[
                                {
                                    "dataIndex": "user_id",
                                    "title": "用户id",
                                    "renderOptions": {
                                        "renderType": "ellipsis-copyable",
                                    },
                                },
                                {
                                    "dataIndex": "user_name",
                                    "title": "用户名",
                                    "renderOptions": {
                                        "renderType": "ellipsis-copyable",
                                    },
                                },
                                {
                                    "dataIndex": "user_role",
                                    "title": "用户角色",
                                    "renderOptions": {"renderType": "tags"},
                                },
                                {
                                    "dataIndex": "操作",
                                    "title": "操作",
                                    "renderOptions": {
                                        "renderType": "button",
                                    },
                                },
                            ],
                            data=refresh_user_manage_table_data(),
                            tableLayout="fixed",
                            filterOptions={
                                "user_name": {
                                    "filterMode": "keyword",
                                },
                                "user_role": {
                                    "filterMode": "checkbox",
                                },
                            },
                            bordered=True,
                            title=fac.AntdSpace(
                                [
                                    fac.AntdButton(
                                        "新增用户",
                                        id="user-manage-add-user",
                                        type="primary",
                                        size="small",
                                    )
                                ]
                            ),
                        )
                    ],
                    direction="vertical",
                    style=style(width="100%"),
                ),
            ],
            False,
        ]

    return dash.no_update


@app.callback(
    [
        Output("user-manage-add-user-modal", "visible"),
        Output("user-manage-add-user-modal", "children"),
    ],
    Input("user-manage-add-user", "nClicks"),
    prevent_initial_call=True,
)
def open_add_user_modal(nClicks):
    """打开新增用户模态框"""

    return [
        True,
        fac.AntdForm(
            [
                fac.AntdFormItem(
                    fac.AntdInput(
                        id="user-manage-add-user-form-user-name",
                        placeholder="请输入用户名",
                        allowClear=True,
                    ),
                    label="用户名",
                ),
                fac.AntdFormItem(
                    fac.AntdInput(
                        id="user-manage-add-user-form-user-password",
                        placeholder="请输入密码",
                        mode="password",
                        allowClear=True,
                    ),
                    label="密码",
                ),
                fac.AntdFormItem(
                    fac.AntdSelect(
                        id="user-manage-add-user-form-user-role",
                        options=[
                            {"label": value["description"], "value": key}
                            for key, value in AuthConfig.roles.items()
                        ],
                        allowClear=False,
                    ),
                    label="用户角色",
                ),
            ],
            id="user-manage-add-user-form",
            key=str(uuid.uuid4()),  # 强制刷新
            enableBatchControl=True,
            layout="vertical",
            values={"user-manage-add-user-form-user-role": AuthConfig.normal_role},
            style=style(marginTop=32),
        ),
    ]


@app.callback(
    Input("user-manage-add-user-modal", "okCounts"),
    [State("user-manage-add-user-form", "values")],
    prevent_initial_call=True,
)
def handle_add_user(okCounts, values):
    """处理新增用户逻辑"""

    # 获取表单数据
    values = values or {}

    # 检查表单数据完整性
    if not (
        values.get("user-manage-add-user-form-user-name")
        and values.get("user-manage-add-user-form-user-password")
    ):
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="请完善用户信息后再提交",
                )
            },
        )

    else:
        # 检查用户名是否重复
        match_user = Users.get_user_by_name(
            values["user-manage-add-user-form-user-name"]
        )

        # 若用户名重复
        if match_user:
            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="error",
                        content="用户名已存在",
                    )
                },
            )

        else:
            # 新增用户
            Users.add_user(
                user_id=str(uuid.uuid4()),
                user_name=values["user-manage-add-user-form-user-name"],
                password_hash=generate_password_hash(
                    values["user-manage-add-user-form-user-password"]
                ),
                user_role=values["user-manage-add-user-form-user-role"],
            )

            # 提示
            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="success",
                        content="用户添加成功",
                    )
                },
            )
            # 关闭modal
            set_props(
                "user-manage-add-user-modal",
                {"visible": False},
            )

            # 刷新用户列表
            set_props(
                "user-manage-table",
                {"data": refresh_user_manage_table_data()},
            )


# 表格栏目高级操作
@app.callback(
    Input("user-manage-table", "nClicksButton"),
    [
        State("user-manage-table", "clickedContent"),
        State("user-manage-table", "recentlyButtonClickedRow"),
    ],
    prevent_initial_call=True,
)
def advanced_user_operation(nClicksButton, clickedContent, recentlyButtonClickedRow):
    """
    处理表格栏高级操作逻辑
    """
    # 处理删除逻辑
    if clickedContent == "删除":
        set_props(
            "user-manage-delete-user-modal",
            {
                "visible": True,
                "children": fac.AntdSpace(
                    [
                        fac.AntdAlert(
                            message=f"是否删除用户{recentlyButtonClickedRow['user_name']}"
                        ),
                        fac.AntdAlert(
                            message="该操作不可逆",
                            type="warning",
                            showIcon=True,
                        ),
                    ],
                    direction="vertical",
                    size="middle",
                    style={"width": "100%"},
                ),
            },
        )

        # 刷新用户列表
        set_props(
            "user-manage-table",
            {"data": refresh_user_manage_table_data()},
        )
    elif clickedContent == "重置密码":
        set_props(
            "user-manage-reset-password-modal",
            {
                "visible": True,
                "children": fac.AntdSpace(
                    [
                        fac.AntdAlert(
                            message=f"是否重置用户{recentlyButtonClickedRow['user_name']}密码"
                        ),
                        fac.AntdAlert(
                            message="该操作不可逆",
                            type="warning",
                            showIcon=True,
                        ),
                    ],
                    direction="vertical",
                    size="middle",
                    style={"width": "100%"},
                ),
            },
        )
    # 重置密码
    elif clickedContent == "重置密码":
        set_props(
            "user-manage-reset-password-modal",
            {
                "visible": True,
                "children": fac.AntdSpace(
                    [
                        fac.AntdAlert(
                            message=f"是否重置用户{recentlyButtonClickedRow['user_name']}密码"
                        ),
                        fac.AntdAlert(
                            message="该操作不可逆",
                            type="warning",
                            showIcon=True,
                        ),
                    ],
                    direction="vertical",
                    size="middle",
                    style={"width": "100%"},
                ),
            },
        )


@app.callback(
    Input("user-manage-delete-user-modal", "okCounts"),
    State("user-manage-table", "recentlyButtonClickedRow"),
    prevent_initial_call=True,
)
def handle_user_delete(okCounts, recentlyButtonClickedRow):
    """模态框处理用户删除逻辑"""
    # 删除用户
    Users.delete_user(user_id=recentlyButtonClickedRow["user_id"])

    set_props(
        "global-message",
        {
            "children": fac.AntdMessage(
                type="success",
                content="用户删除成功",
            )
        },
    )
    time.sleep(0.5)
    set_props(
        "user-manage-delete-user-modal",
        {"visible": False},
    )

    # 刷新用户列表
    set_props(
        "user-manage-table",
        {"data": refresh_user_manage_table_data()},
    )


@app.callback(
    Input("user-manage-reset-password-modal", "okCounts"),
    State("user-manage-table", "recentlyButtonClickedRow"),
    prevent_initial_call=True,
)
def handle_user_reset_password(okCounts, recentlyButtonClickedRow):
    """模态框处理用户重置密码逻辑"""

    # 定义密码字符集
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    # 生成 12 位随机密码
    new_password = "".join(secrets.choice(characters) for _ in range(8))

    Users.update_user(
        user_id=recentlyButtonClickedRow["user_id"],
        password_hash=generate_password_hash(new_password),
    )
    # 重置密码
    set_props(
        "global-message",
        {
            "children": [
                fac.AntdMessage(
                    type="success",
                    content=f"用户{recentlyButtonClickedRow['user_name']}密码重置为  {new_password}",
                ),
            ]
        },
    )

    time.sleep(0.5)
    set_props(
        "user-manage-reset-password-modal",
        {"visible": False},
    )

    # 刷新用户列表
    set_props(
        "user-manage-table",
        {"data": refresh_user_manage_table_data()},
    )
