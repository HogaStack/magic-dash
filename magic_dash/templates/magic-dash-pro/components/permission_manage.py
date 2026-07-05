import time
import dash
from dash import set_props
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style
from dash.dependencies import Input, Output, State

from server import app
from configs import AuthConfig, RouterConfig
from models.user_permission_groups import UserPermissionGroups
from models.exceptions import InvalidPermissionGroupError, ExistingPermissionGroupError


def render():
    """渲染权限管理抽屉"""

    return fac.AntdDrawer(
        id="permission-manage-drawer",
        title=fac.AntdSpace([fac.AntdIcon(icon="antd-safety"), "权限管理"]),
        width="70vw",
    )


def get_permission_page_options():
    """获取可用于权限规则配置的页面选项"""

    return [
        {
            "label": title,
            "value": pathname,
        }
        for pathname, title in RouterConfig.valid_pathnames.items()
        if pathname in UserPermissionGroups.get_valid_access_rule_keys()
        and pathname != RouterConfig.index_pathname
    ]


def get_access_rule_type_options():
    """获取页面访问规则类型选项"""

    return [
        {"label": "可访问全部页面", "value": "all"},
        {"label": "仅可访问指定页面", "value": "include"},
        {"label": "不可访问指定页面", "value": "exclude"},
    ]


def get_access_rule_type_tag(access_rule_type):
    """获取页面访问规则类型tag渲染数据"""

    access_rule_type_map = {
        "all": {"tag": "全部可访问", "color": "green"},
        "include": {"tag": "包含指定", "color": "blue"},
        "exclude": {"tag": "排除指定", "color": "orange"},
    }

    return access_rule_type_map.get(
        access_rule_type,
        {"tag": "未知规则", "color": "red"},
    )


def get_conflict_status_tag(conflict_type, conflict_label):
    """获取冲突状态tag渲染数据"""

    conflict_status_color_map = {
        None: "green",
        "admin_database_forbidden": "red",
        "config_override": "orange",
        "config_name_conflict": "red",
        "invalid_access_rule": "red",
    }

    return {
        "tag": conflict_label or "正常",
        "color": conflict_status_color_map.get(conflict_type, "red"),
    }


def format_access_rule_keys(access_rule_type, access_rule_keys):
    """格式化页面访问规则keys表格展示文案"""

    if access_rule_type == "all":
        return "全部页面"

    if not access_rule_keys:
        return "无"

    return "、".join(access_rule_keys)


def refresh_permission_manage_table_data():
    """当前模块内复用工具函数，刷新权限管理表格数据"""

    return [
        {
            "权限来源": {
                "tag": item["source_label"],
                "color": "gold" if item["source"] == "config" else "blue",
            },
            "permission_group_id": item["permission_group_id"],
            "permission_group_name": item["permission_group_name"],
            "access_rule_type": get_access_rule_type_tag(item["access_rule_type"]),
            "conflict_status": get_conflict_status_tag(
                item["conflict_type"],
                item["conflict_label"],
            ),
            "access_rule_keys": format_access_rule_keys(
                item["access_rule_type"],
                item["access_rule_keys"],
            ),
            "source": item["source"],
            "conflict_type": item["conflict_type"],
            "conflict_message": item["conflict_message"],
            "database_exists": item["database_exists"],
            "is_admin": item["is_admin"],
            "操作": [
                {
                    "content": "编辑",
                    "type": "link",
                    "disabled": item["is_admin"],
                },
                {
                    "content": "删除",
                    "type": "link",
                    "danger": True,
                    "disabled": item["is_admin"] or not item["database_exists"],
                    "popConfirmProps": {
                        "title": "确认删除当前权限组",
                        "okText": "确认",
                        "cancelText": "取消",
                    },
                },
            ],
        }
        for item in UserPermissionGroups.get_effective_permission_group_records()
    ]


def show_permission_manage_error(content):
    """显示权限管理错误提示"""

    set_props(
        "global-message",
        {
            "children": fac.AntdMessage(
                type="error",
                content=content,
            )
        },
    )


def build_permission_group_form(mode, permission_group=None):
    """构建新增或编辑权限组表单"""

    permission_group = permission_group or {}
    is_edit_mode = mode == "edit"
    permission_group_id = permission_group.get("permission_group_id")
    access_rule_type = permission_group.get("access_rule_type", "exclude")

    children = []

    if is_edit_mode and permission_group.get("source") == "config":
        children.append(
            fac.AntdAlert(
                message="当前为硬编码权限组，保存后将以数据库配置覆盖其非admin权限规则。",
                type="info",
                showIcon=True,
            )
        )

    if is_edit_mode and permission_group.get("conflict_message"):
        children.append(
            fac.AntdAlert(
                message=permission_group["conflict_message"],
                type="warning",
                showIcon=True,
            )
        )

    children.append(
        fac.AntdForm(
            [
                fac.AntdFormItem(
                    fac.AntdInput(
                        id=f"permission-manage-{mode}-form-permission-group-id",
                        placeholder="请输入权限组id",
                        readOnly=is_edit_mode,
                        allowClear=not is_edit_mode,
                    ),
                    label="权限组id",
                ),
                fac.AntdFormItem(
                    fac.AntdInput(
                        id=f"permission-manage-{mode}-form-permission-group-name",
                        placeholder="请输入权限组名称",
                        allowClear=True,
                    ),
                    label="权限组名称",
                ),
                fac.AntdFormItem(
                    fac.AntdSelect(
                        id=f"permission-manage-{mode}-form-access-rule-type",
                        options=get_access_rule_type_options(),
                        allowClear=False,
                    ),
                    label="页面访问规则类型",
                ),
                fac.AntdFormItem(
                    fac.AntdSelect(
                        id=f"permission-manage-{mode}-form-access-rule-keys",
                        options=get_permission_page_options(),
                        mode="multiple",
                        placeholder="请选择页面",
                        allowClear=True,
                        maxTagCount="responsive",
                    ),
                    label="页面访问规则keys",
                    tooltip="规则类型为“可访问全部页面”时，本项会自动忽略",
                ),
            ],
            id=f"permission-manage-{mode}-form",
            enableBatchControl=True,
            layout="vertical",
            values={
                f"permission-manage-{mode}-form-permission-group-id": permission_group_id,
                f"permission-manage-{mode}-form-permission-group-name": permission_group.get(
                    "permission_group_name"
                ),
                f"permission-manage-{mode}-form-access-rule-type": access_rule_type,
                f"permission-manage-{mode}-form-access-rule-keys": permission_group.get(
                    "access_rule_keys", []
                ),
            },
            style=style(marginTop=16),
        )
    )

    return fac.AntdSpace(
        children,
        direction="vertical",
        style=style(width="100%"),
    )


def get_permission_group_by_effective_records(permission_group_id):
    """根据权限组id从有效权限组记录中查询权限组信息"""

    for item in UserPermissionGroups.get_effective_permission_group_records():
        if item["permission_group_id"] == permission_group_id:
            return item

    return None


def validate_permission_group_form_values(values, mode):
    """校验权限组表单数据"""

    values = values or {}

    permission_group_id = (
        values.get(f"permission-manage-{mode}-form-permission-group-id") or ""
    ).strip()
    permission_group_name = (
        values.get(f"permission-manage-{mode}-form-permission-group-name") or ""
    ).strip()
    access_rule_type = values.get(f"permission-manage-{mode}-form-access-rule-type")
    access_rule_keys = (
        values.get(f"permission-manage-{mode}-form-access-rule-keys") or []
    )

    if not (permission_group_id and permission_group_name and access_rule_type):
        raise InvalidPermissionGroupError("请完善权限组信息后再提交")

    if permission_group_id == AuthConfig.admin_role:
        raise InvalidPermissionGroupError("admin权限组不允许存储为数据库权限组")

    if mode == "add":
        effective_roles = UserPermissionGroups.get_effective_roles()
        if permission_group_id in effective_roles:
            raise ExistingPermissionGroupError("权限分组id已存在")

        if permission_group_name in [
            item["description"] for item in effective_roles.values()
        ]:
            raise ExistingPermissionGroupError("权限分组名称已存在")

    access_rule = UserPermissionGroups.normalize_access_rule(
        access_rule_type,
        access_rule_keys,
    )

    return {
        "permission_group_id": permission_group_id,
        "permission_group_name": permission_group_name,
        "access_rule_type": access_rule["type"],
        "access_rule_keys": access_rule["keys"],
    }


@app.callback(
    [
        Output("permission-manage-drawer", "children"),
        Output("permission-manage-drawer", "loading", allow_duplicate=True),
    ],
    Input("permission-manage-drawer", "visible"),
    prevent_initial_call=True,
)
def render_permission_manage_drawer(visible):
    """每次权限管理抽屉打开后，动态更新内容"""

    if visible:
        time.sleep(0.5)

        return [
            [
                # 新增权限组模态框
                fac.AntdModal(
                    id="permission-manage-add-permission-group-modal",
                    title=fac.AntdSpace(
                        [fac.AntdIcon(icon="antd-plus"), "新增权限组"]
                    ),
                    mask=False,
                    renderFooter=True,
                    okClickClose=False,
                    width=780,
                ),
                # 编辑权限组模态框
                fac.AntdModal(
                    id="permission-manage-edit-permission-group-modal",
                    title=fac.AntdSpace(
                        [fac.AntdIcon(icon="antd-edit"), "编辑权限组"]
                    ),
                    mask=False,
                    renderFooter=True,
                    okClickClose=False,
                    width=780,
                ),
                fac.AntdSpace(
                    [
                        fac.AntdTable(
                            id="permission-manage-table",
                            columns=[
                                {
                                    "dataIndex": "权限来源",
                                    "title": "权限来源",
                                    "renderOptions": {"renderType": "tags"},
                                },
                                {
                                    "dataIndex": "permission_group_id",
                                    "title": "权限组id",
                                    "renderOptions": {
                                        "renderType": "ellipsis-copyable",
                                    },
                                },
                                {
                                    "dataIndex": "permission_group_name",
                                    "title": "权限组名称",
                                    "renderOptions": {
                                        "renderType": "ellipsis-copyable",
                                    },
                                },
                                {
                                    "dataIndex": "access_rule_type",
                                    "title": "访问规则",
                                    "renderOptions": {"renderType": "tags"},
                                },
                                {
                                    "dataIndex": "conflict_status",
                                    "title": "冲突状态",
                                    "renderOptions": {"renderType": "tags"},
                                },
                                {
                                    "dataIndex": "access_rule_keys",
                                    "title": "规则keys",
                                    "renderOptions": {
                                        "renderType": "ellipsis-copyable",
                                    },
                                },
                                {
                                    "dataIndex": "source",
                                    "title": "来源标识",
                                    "hidden": True,
                                },
                                {
                                    "dataIndex": "conflict_type",
                                    "title": "冲突类型",
                                    "hidden": True,
                                },
                                {
                                    "dataIndex": "conflict_message",
                                    "title": "冲突说明",
                                    "hidden": True,
                                },
                                {
                                    "dataIndex": "database_exists",
                                    "title": "数据库记录是否存在",
                                    "hidden": True,
                                },
                                {
                                    "dataIndex": "is_admin",
                                    "title": "是否admin权限组",
                                    "hidden": True,
                                },
                                {
                                    "dataIndex": "操作",
                                    "title": "操作",
                                    "renderOptions": {
                                        "renderType": "button",
                                    },
                                },
                            ],
                            data=refresh_permission_manage_table_data(),
                            tableLayout="fixed",
                            filterOptions={
                                "权限来源": {
                                    "filterMode": "checkbox",
                                },
                                "permission_group_id": {
                                    "filterMode": "keyword",
                                },
                                "permission_group_name": {
                                    "filterMode": "keyword",
                                },
                                "access_rule_type": {
                                    "filterMode": "checkbox",
                                },
                                "conflict_status": {
                                    "filterMode": "checkbox",
                                },
                            },
                            bordered=True,
                            title=fac.AntdSpace(
                                [
                                    fac.AntdButton(
                                        "新增权限组",
                                        id="permission-manage-add-permission-group",
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
        Output("permission-manage-add-permission-group-modal", "visible"),
        Output("permission-manage-add-permission-group-modal", "children"),
    ],
    Input("permission-manage-add-permission-group", "nClicks"),
    prevent_initial_call=True,
)
def open_add_permission_group_modal(nClicks):
    """打开新增权限组模态框"""

    return [
        True,
        build_permission_group_form(
            "add",
            {
                "access_rule_type": "exclude",
                "access_rule_keys": [],
            },
        ),
    ]


@app.callback(
    Input("permission-manage-add-permission-group-modal", "okCounts"),
    State("permission-manage-add-form", "values"),
    prevent_initial_call=True,
)
def handle_add_permission_group(okCounts, values):
    """处理新增权限组逻辑"""

    try:
        form_values = validate_permission_group_form_values(values, "add")
        UserPermissionGroups.add_permission_group(**form_values)
    except (InvalidPermissionGroupError, ExistingPermissionGroupError) as e:
        show_permission_manage_error(str(e))
        return

    set_props(
        "global-message",
        {
            "children": fac.AntdMessage(
                type="success",
                content="权限组添加成功",
            )
        },
    )

    set_props("permission-manage-add-permission-group-modal", {"visible": False})
    set_props(
        "permission-manage-table",
        {"data": refresh_permission_manage_table_data()},
    )


@app.callback(
    Input("permission-manage-table", "nClicksButton"),
    [
        State("permission-manage-table", "clickedContent"),
        State("permission-manage-table", "recentlyButtonClickedRow"),
    ],
    prevent_initial_call=True,
)
def handle_permission_group_action(
    nClicksButton,
    clickedContent,
    recentlyButtonClickedRow,
):
    """处理权限组表格操作逻辑"""

    if clickedContent not in ["编辑", "删除"]:
        return

    permission_group_id = (recentlyButtonClickedRow or {}).get("permission_group_id")

    if not isinstance(permission_group_id, str):
        show_permission_manage_error("权限组信息不正确")
        return

    if permission_group_id == AuthConfig.admin_role:
        show_permission_manage_error("admin权限组不允许删除或编辑")
        return

    match_group = get_permission_group_by_effective_records(permission_group_id)

    if not match_group:
        show_permission_manage_error("权限组不存在或已被删除")
        return

    if clickedContent == "编辑":
        set_props(
            "permission-manage-edit-permission-group-modal",
            {
                "visible": True,
                "children": build_permission_group_form("edit", match_group),
            },
        )

    elif clickedContent == "删除":
        if not match_group["database_exists"]:
            show_permission_manage_error("当前权限组不存在可删除的数据库配置")
            return

        try:
            UserPermissionGroups.delete_permission_group(
                permission_group_id=permission_group_id,
                include_builtin=permission_group_id in AuthConfig.roles,
                ignore_user_reference=permission_group_id in AuthConfig.roles,
            )
        except InvalidPermissionGroupError as e:
            show_permission_manage_error(str(e))
            return

        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="success",
                    content="权限组删除成功",
                )
            },
        )

        set_props(
            "permission-manage-table",
            {"data": refresh_permission_manage_table_data()},
        )


@app.callback(
    Input("permission-manage-edit-permission-group-modal", "okCounts"),
    State("permission-manage-edit-form", "values"),
    prevent_initial_call=True,
)
def handle_edit_permission_group(okCounts, values):
    """处理编辑权限组逻辑"""

    try:
        form_values = validate_permission_group_form_values(values, "edit")

        if form_values["permission_group_id"] == AuthConfig.admin_role:
            raise InvalidPermissionGroupError("admin权限组不允许编辑")

        UserPermissionGroups.upsert_permission_group(
            include_builtin=form_values["permission_group_id"] in AuthConfig.roles,
            **form_values,
        )
    except (InvalidPermissionGroupError, ExistingPermissionGroupError) as e:
        show_permission_manage_error(str(e))
        return

    set_props(
        "global-message",
        {
            "children": fac.AntdMessage(
                type="success",
                content="权限组更新成功",
            )
        },
    )

    set_props("permission-manage-edit-permission-group-modal", {"visible": False})
    set_props(
        "permission-manage-table",
        {"data": refresh_permission_manage_table_data()},
    )
