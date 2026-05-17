import feffery_antd_components as fac
import feffery_utils_components as fuc
from feffery_dash_utils.style_utils import style

from models.logs import LoginLogs

# 令对应当前页面的回调函数子模块生效
import callbacks.core_pages_c.login_logs_c  # noqa: F401


def render():
    """子页面：系统管理-日志管理-登录日志"""

    return [
        # 稳定触发初始化数据加载
        fuc.FefferyTimeout(id="core-login-logs-table-init-data-trigger", delay=0),
        fac.AntdSpace(
            [
                fac.AntdBreadcrumb(
                    items=[
                        {"title": "系统管理"},
                        {"title": "日志管理"},
                        {"title": "登录日志"},
                    ]
                ),
                fac.AntdSpin(
                    fac.AntdTable(
                        id="core-login-logs-table",
                        columns=[
                            {
                                "dataIndex": "id",
                                "title": "记录id",
                            },
                            {
                                "dataIndex": "user_name",
                                "title": "登录用户名称",
                            },
                            {
                                "dataIndex": "user_id",
                                "title": "登录用户id",
                                "hidden": True,
                            },
                            {
                                "dataIndex": "ip",
                                "title": "登录ip",
                            },
                            {
                                "dataIndex": "browser",
                                "title": "浏览器",
                            },
                            {
                                "dataIndex": "os",
                                "title": "操作系统",
                            },
                            {
                                "dataIndex": "status",
                                "title": "登录状态",
                                "renderOptions": {"renderType": "tags"},
                            },
                            {
                                "dataIndex": "login_datetime",
                                "title": "登录时间",
                            },
                        ],
                        pagination={
                            "current": 1,
                            "total": LoginLogs.get_count(),  # 获取登录日志最新记录数
                            "pageSize": 10,
                            "showSizeChanger": False,
                        },
                        mode="server-side",  # 使用服务端数据分页模式
                        bordered=True,
                        tableLayout="fixed",
                        rowSelectionType="checkbox",
                        sortOptions={
                            "sortDataIndexes": [
                                "id",
                                "user_name",
                                "status",
                                "login_datetime",
                            ],
                        },
                        filterOptions={
                            "user_name": {
                                "filterMode": "keyword",
                            }
                        },
                        title=fac.AntdSpace(
                            [
                                fac.AntdButton(
                                    "刷新",
                                    id="core-login-logs-refresh-data",
                                    color="primary",
                                    variant="filled",
                                ),
                                fac.AntdPopconfirm(
                                    fac.AntdButton(
                                        "删除",
                                        id="core-login-logs-delete-data",
                                        color="danger",
                                        variant="filled",
                                    ),
                                    id="core-login-logs-delete-data-confirm",
                                    title="删除记录",
                                    description="删除已选中记录，请谨慎操作",
                                ),
                                fac.AntdPopconfirm(
                                    fac.AntdButton(
                                        "清空",
                                        id="core-login-logs-truncate-data",
                                        color="danger",
                                        variant="filled",
                                    ),
                                    id="core-login-logs-truncate-data-confirm",
                                    title="清空记录",
                                    description="清空全部记录，请谨慎操作",
                                ),
                                fac.AntdPopconfirm(
                                    fac.AntdButton(
                                        "导出",
                                        id="core-login-logs-export-data",
                                        color="default",
                                        variant="filled",
                                        loadingChildren="导出中",
                                    ),
                                    id="core-login-logs-export-data-confirm",
                                    title="导出数据",
                                    description="导出全部记录数据",
                                ),
                            ],
                            size=3,
                        ),
                    ),
                    delay=300,
                ),
            ],
            direction="vertical",
            style=style(width="100%"),
        ),
    ]
