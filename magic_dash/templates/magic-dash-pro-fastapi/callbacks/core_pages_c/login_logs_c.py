import io
import csv
import time

import dash
from datetime import datetime
from dash import set_props, dcc
import feffery_antd_components as fac
from dash.dependencies import Input, Output, State

from server import app
from models.logs import LoginLogs


@app.callback(
    Output("core-login-logs-table", "data"),
    [
        Input("core-login-logs-table-init-data-trigger", "timeoutCount"),
        Input("core-login-logs-table", "pagination"),
        Input("core-login-logs-table", "sorter"),
        Input("core-login-logs-table", "filter"),
    ],
    prevent_initial_call=True,
)
def handle_login_logs_table_data_load(timeoutCount, pagination, sorter, _filter):
    """处理登录日志表数据加载"""

    # 为本次查询构造查询条件
    query_condition = {}

    # 若存在有效排序条件
    if sorter and sorter["columns"]:
        query_condition["order_by"] = sorter["columns"][0]
        query_condition["order"] = sorter["orders"][0]

    # 若存在有效筛选条件
    if _filter:
        if _filter.get("user_name"):
            query_condition["user_name_keyword"] = _filter["user_name"][0]

    # 获取登录日志数据
    match_login_logs = LoginLogs.get_logs(
        limit=pagination["pageSize"],
        offset=(pagination["current"] - 1) * pagination["pageSize"],
        **query_condition,  # 传入实际查询条件
    )

    return [
        {
            **item,
            "status": {
                "tag": item["status"],
                "color": "green" if item["status"] == "登录成功" else "red",
            },
            "login_datetime": item["login_datetime"].strftime("%Y-%m-%d %H:%M:%S"),
            "key": item["id"],
        }
        for item in match_login_logs
    ]


@app.callback(
    [
        Input("core-login-logs-refresh-data", "nClicks"),
        Input("core-login-logs-delete-data-confirm", "confirmCounts"),
        Input("core-login-logs-truncate-data-confirm", "confirmCounts"),
    ],
    State("core-login-logs-table", "selectedRowKeys"),
)
def handle_login_logs_refresh_delete_truncate(*args):
    """处理刷新、删除、清空操作"""

    # 若本次为刷新操作
    if dash.ctx.triggered_id == "core-login-logs-refresh-data":
        # 消息提示
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="success", content="登录日志数据刷新成功"
                )
            },
        )

    # 若本次为删除操作
    elif dash.ctx.triggered_id == "core-login-logs-delete-data-confirm":
        # 确定要删除的目标记录行key值列表
        target_keys = dash.ctx.states["core-login-logs-table.selectedRowKeys"] or []

        # 若当前无已选择行
        if not target_keys:
            # 消息提示
            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="warning", content="请先选择要删除的登录日志记录行"
                    )
                },
            )
        else:
            # 执行针对目标记录行的删除操作
            LoginLogs.delete_logs(log_ids=target_keys)
            # 消息提示
            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="success", content="相关登录日志记录删除成功"
                    )
                },
            )

    # 若本次为清空操作
    elif dash.ctx.triggered_id == "core-login-logs-truncate-data-confirm":
        # 执行针对登录日志记录的清空操作
        LoginLogs.truncate_logs()
        # 消息提示
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="success", content="登录日志记录清空成功"
                )
            },
        )

    # 处理上述各操作之后的数据表更新
    set_props(
        "core-login-logs-table",
        {
            # 重置分页参数
            "pagination": {
                "current": 1,
                "total": LoginLogs.get_count(),  # 获取登录日志最新记录数
                "pageSize": 10,
                "showSizeChanger": False,
            },
            # 重置已选择行
            "selectedRowKeys": [],
        },
    )


@app.callback(
    Input("core-login-logs-export-data-confirm", "confirmCounts"),
    running=[(Output("core-login-logs-export-data", "loading"), True, False)],
)
def handle_login_logs_export_data(confirmCounts):
    """处理导出数据操作"""

    # 适当增加加载动画时长
    time.sleep(0.5)

    # 查询全部数据记录
    all_login_logs = LoginLogs.get_logs()

    # 若登录日志记录不为空
    if all_login_logs:
        # 处理登录时间字段格式
        for item in all_login_logs:
            item["login_datetime"] = item["login_datetime"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        # 生成CSV字符串
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=all_login_logs[0].keys())
        writer.writeheader()
        writer.writerows(all_login_logs)
        csv_string = output.getvalue()

        # 返回下载文件流
        set_props(
            "global-download",
            {
                "data": dcc.send_string(
                    csv_string,
                    "登录日志导出结果{}.csv".format(
                        datetime.now().strftime("%Y%m%d%H%M%S")
                    ),
                    type="text/csv",
                )
            },
        )
        # 消息提示
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="success", content="登录日志记录导出成功"
                )
            },
        )

    else:
        # 消息提示
        set_props(
            "global-message",
            {"children": fac.AntdMessage(type="warning", content="当前无登录日志记录")},
        )
