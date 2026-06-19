import uuid
import time
import dash
from dash import set_props
from flask_login import current_user
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style
from dash.dependencies import Input, Output, State
from werkzeug.security import generate_password_hash

from server import app
from models.users import Users
from utils.validation_utils import validate_optional_email


def render():
    """渲染个人信息模态框"""

    return fac.AntdModal(
        id="personal-info-modal",
        title=fac.AntdSpace([fac.AntdIcon(icon="antd-user"), "个人信息"]),
        renderFooter=True,
        okClickClose=False,
    )


@app.callback(
    [
        Output("personal-info-modal", "children"),
        Output("personal-info-modal", "loading", allow_duplicate=True),
    ],
    Input("personal-info-modal", "visible"),
    prevent_initial_call=True,
)
def render_personal_info_modal(visible):
    """每次个人信息模态框打开后，动态更新内容"""

    if visible:
        time.sleep(0.5)

        # 查询当前用户信息
        match_user = Users.get_user(current_user.id)

        return [
            fac.AntdForm(
                [
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="personal-info-user-name",
                            placeholder="请输入用户名",
                            allowClear=True,
                        ),
                        label="用户名",
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="personal-info-user-email",
                            placeholder="请输入邮箱",
                            allowClear=True,
                        ),
                        label="邮箱",
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="personal-info-user-password",
                            placeholder="请输入新的密码",
                            mode="password",
                            allowClear=True,
                        ),
                        label="密码",
                        tooltip="一旦填写并确定更新，则视作新的密码",
                    ),
                ],
                id="personal-info-form",
                key=str(uuid.uuid4()),  # 强制刷新
                enableBatchControl=True,
                layout="vertical",
                values={
                    "personal-info-user-name": match_user.user_name,
                    "personal-info-user-email": match_user.user_email or "",
                },
                style=style(marginTop=32),
            ),
            False,
        ]

    return dash.no_update


@app.callback(
    Input("personal-info-modal", "okCounts"),
    [State("personal-info-form", "values")],
    prevent_initial_call=True,
)
def handle_personal_info_update(okCounts, values):
    """处理个人信息更新逻辑"""

    # 获取表单数据
    values = values or {}

    # 检查表单数据完整性
    if not values.get("personal-info-user-name"):
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
        user_email = (values.get("personal-info-user-email") or "").strip()

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
        match_user = Users.get_user_by_name(values["personal-info-user-name"])

        # 若与其他用户用户名重复
        if match_user and match_user.user_id != current_user.id:
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
            update_kwargs = {
                "user_name": values["personal-info-user-name"],
                "user_email": user_email or None,
            }

            # 更新用户信息
            if values.get("personal-info-user-password"):
                # 同时更新密码散列值
                update_kwargs["password_hash"] = generate_password_hash(
                    values["personal-info-user-password"]
                )

            Users.update_user(user_id=current_user.id, **update_kwargs)

            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="success",
                        content="用户信息更新成功，页面即将刷新",
                    )
                },
            )
            # 页面延时刷新
            set_props(
                "global-reload",
                {"reload": True, "delay": 2000},
            )
