import uuid
import time
import dash
from dash import set_props
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style
from dash.dependencies import Input, Output, State
from werkzeug.security import generate_password_hash

from server import app
from models.users import Users
from models.departments import Departments
from models.exceptions import ExistingUserError

from configs import AuthConfig
from utils.validation_utils import validate_optional_email


def render():
    """渲染用户管理抽屉"""

    return fac.AntdDrawer(
        id="user-manage-drawer",
        title=fac.AntdSpace([fac.AntdIcon(icon="antd-team"), "用户管理"]),
        width="65vw",
    )


def refresh_user_manage_table_data():
    """当前模块内复用工具函数，刷新用户管理表格数据"""

    # 查询全部用户信息（含部门名称）
    all_users = Users.get_all_users(with_department_name=True)

    return [
        {
            "user_id": item["user_id"],
            "user_name": item["user_name"],
            "user_email": item["user_email"] or "无",
            "user_department": item["department_name"] or "无",
            "user_role": {
                "tag": AuthConfig.roles.get(item["user_role"])["description"],
                "color": (
                    "gold" if item["user_role"] == AuthConfig.admin_role else "blue"
                ),
            },
            "操作": (
                (
                    [
                        {
                            "content": "编辑",
                            "type": "link",
                        }
                    ]
                    if item["user_role"] != AuthConfig.admin_role
                    else []
                )
                + [
                    {
                        "content": "删除",
                        "type": "link",
                        "danger": True,
                        "disabled": item["user_role"] == AuthConfig.admin_role,
                        "popConfirmProps": {
                            "title": "确认删除当前用户",
                            "okText": "确认",
                            "cancelText": "取消",
                        },
                    }
                ]
            ),
        }
        for item in all_users
    ]


def check_department_id_valid(department_id):
    """检查部门id是否为空或对应有效部门"""

    if department_id in [None, ""]:
        return True

    if not isinstance(department_id, str):
        return False

    return Departments.get_department(department_id) is not None


def show_user_manage_error(content):
    """显示用户管理错误提示"""

    set_props(
        "global-message",
        {
            "children": fac.AntdMessage(
                type="error",
                content=content,
            )
        },
    )


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
                # 编辑用户模态框
                fac.AntdModal(
                    id="user-manage-edit-user-modal",
                    title=fac.AntdSpace(
                        [fac.AntdIcon(icon="antd-edit"), "编辑用户"]
                    ),
                    mask=False,
                    renderFooter=True,
                    okClickClose=False,
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
                                    "dataIndex": "user_email",
                                    "title": "邮箱",
                                    "renderOptions": {
                                        "renderType": "ellipsis-copyable",
                                    },
                                },
                                {
                                    "dataIndex": "user_department",
                                    "title": "所属部门",
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
                                "user_email": {
                                    "filterMode": "keyword",
                                },
                                "user_department": {
                                    "filterMode": "checkbox",
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

    # 查询当前全部部门信息
    departments = Departments.get_all_departments()

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
                        id="user-manage-add-user-form-user-email",
                        placeholder="请输入邮箱",
                        allowClear=True,
                    ),
                    label="邮箱",
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
                        id="user-manage-add-user-form-department-id",
                        options=[
                            {
                                "label": item["department_name"],
                                "value": item["department_id"],
                            }
                            for item in departments
                        ],
                        placeholder="请选择所属部门",
                        allowClear=True,
                    ),
                    label="所属部门",
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
        user_email = (values.get("user-manage-add-user-form-user-email") or "").strip()

        if not validate_optional_email(user_email):
            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="error",
                        content="邮箱格式不正确",
                    )
                },
            )
            return

        # 检查用户名是否重复
        match_user = Users.get_user_by_name(
            values["user-manage-add-user-form-user-name"]
        )
        match_email_user = Users.get_user_by_email(user_email)

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

        # 若非空邮箱已被其他用户使用
        elif match_email_user:
            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="error",
                        content="邮箱已被其他用户使用",
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
                user_email=user_email or None,
                department_id=values.get("user-manage-add-user-form-department-id"),
                user_role=values["user-manage-add-user-form-user-role"],
            )

            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="success",
                        content="用户添加成功",
                    )
                },
            )

            # 刷新用户列表
            set_props(
                "user-manage-table",
                {"data": refresh_user_manage_table_data()},
            )


def build_edit_user_form(match_user):
    """构建编辑用户表单"""

    # 查询当前全部部门信息
    departments = Departments.get_all_departments()

    return fac.AntdForm(
        [
            fac.AntdFormItem(
                fac.AntdInput(
                    id="user-manage-edit-user-form-user-id",
                    readOnly=True,
                ),
                label="用户id",
            ),
            fac.AntdFormItem(
                fac.AntdInput(
                    id="user-manage-edit-user-form-user-name",
                    readOnly=True,
                ),
                label="用户名",
            ),
            fac.AntdFormItem(
                fac.AntdInput(
                    id="user-manage-edit-user-form-user-email",
                    placeholder="请输入邮箱",
                    allowClear=True,
                ),
                label="邮箱",
            ),
            fac.AntdFormItem(
                fac.AntdSelect(
                    id="user-manage-edit-user-form-department-id",
                    options=[
                        {
                            "label": item["department_name"],
                            "value": item["department_id"],
                        }
                        for item in departments
                    ],
                    placeholder="请选择所属部门",
                    allowClear=True,
                ),
                label="所属部门",
            ),
            fac.AntdFormItem(
                fac.AntdSelect(
                    id="user-manage-edit-user-form-user-role",
                    options=[
                        {"label": value["description"], "value": key}
                        for key, value in AuthConfig.roles.items()
                    ],
                    allowClear=False,
                ),
                label="用户角色",
            ),
        ],
        id="user-manage-edit-user-form",
        key=str(uuid.uuid4()),  # 强制刷新
        enableBatchControl=True,
        layout="vertical",
        values={
            "user-manage-edit-user-form-user-id": match_user.user_id,
            "user-manage-edit-user-form-user-name": match_user.user_name,
            "user-manage-edit-user-form-user-email": match_user.user_email or "",
            "user-manage-edit-user-form-department-id": match_user.department_id,
            "user-manage-edit-user-form-user-role": match_user.user_role,
        },
        style=style(marginTop=32),
    )


@app.callback(
    Input("user-manage-table", "nClicksButton"),
    [
        State("user-manage-table", "clickedContent"),
        State("user-manage-table", "recentlyButtonClickedRow"),
    ],
    prevent_initial_call=True,
)
def handle_user_action(nClicksButton, clickedContent, recentlyButtonClickedRow):
    """处理用户表格操作逻辑"""

    if clickedContent not in ["编辑", "删除"]:
        return

    user_id = (recentlyButtonClickedRow or {}).get("user_id")

    if not isinstance(user_id, str):
        show_user_manage_error("用户信息不正确")
        return

    match_user = Users.get_user(user_id)

    if not match_user:
        show_user_manage_error("用户不存在或已被删除")
        return

    if match_user.user_role == AuthConfig.admin_role:
        show_user_manage_error("管理员用户不允许删除或编辑")
        return

    if clickedContent == "编辑":
        set_props(
            "user-manage-edit-user-modal",
            {
                "visible": True,
                "children": build_edit_user_form(match_user),
            },
        )

    elif clickedContent == "删除":
        # 删除用户
        Users.delete_user(user_id=match_user.user_id)

        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="success",
                    content="用户删除成功",
                )
            },
        )

        # 刷新用户列表
        set_props(
            "user-manage-table",
            {"data": refresh_user_manage_table_data()},
        )


@app.callback(
    Input("user-manage-edit-user-modal", "okCounts"),
    State("user-manage-edit-user-form", "values"),
    prevent_initial_call=True,
)
def handle_edit_user(okCounts, values):
    """处理编辑用户逻辑"""

    # 获取表单数据
    values = values or {}

    user_id = values.get("user-manage-edit-user-form-user-id")
    user_role = values.get("user-manage-edit-user-form-user-role")
    department_id = values.get("user-manage-edit-user-form-department-id")

    # 检查表单数据完整性
    if not (user_id and user_role):
        show_user_manage_error("请完善用户信息后再提交")
        return

    if not isinstance(user_id, str):
        show_user_manage_error("用户信息不正确")
        return

    user_email = values.get("user-manage-edit-user-form-user-email") or ""
    if not isinstance(user_email, str):
        show_user_manage_error("邮箱格式不正确")
        return

    user_email = user_email.strip()

    if not validate_optional_email(user_email):
        show_user_manage_error("邮箱格式不正确")
        return

    if not isinstance(user_role, str) or user_role not in AuthConfig.roles:
        show_user_manage_error("用户角色不正确")
        return

    if not check_department_id_valid(department_id):
        show_user_manage_error("所属部门不存在或已被删除")
        return
    department_id = department_id or None

    match_user = Users.get_user(user_id)
    match_email_user = Users.get_user_by_email(user_email)

    if not match_user:
        show_user_manage_error("用户不存在或已被删除")
        return

    if match_user.user_role == AuthConfig.admin_role:
        show_user_manage_error("管理员用户不允许删除或编辑")
        return

    # 若非空邮箱已被其他用户使用
    if match_email_user and match_email_user.user_id != user_id:
        show_user_manage_error("邮箱已被其他用户使用")
        return

    # 更新用户
    try:
        Users.update_user(
            user_id=user_id,
            user_email=user_email or None,
            department_id=department_id,
            user_role=user_role,
        )
    except ExistingUserError as e:
        show_user_manage_error(str(e))
        return

    set_props(
        "global-message",
        {
            "children": fac.AntdMessage(
                type="success",
                content="用户信息更新成功",
            )
        },
    )

    set_props("user-manage-edit-user-modal", {"visible": False})

    # 刷新用户列表
    set_props(
        "user-manage-table",
        {"data": refresh_user_manage_table_data()},
    )
