import dash
from dash import html, set_props
import feffery_antd_components as fac
import feffery_utils_components as fuc
from feffery_dash_utils.style_utils import style
from dash.dependencies import Input, Output, State
from feffery_dash_utils.version_utils import (
    check_python_version,
    check_dependencies_version,
)

# 检查Python版本
check_python_version(min_version="3.8", max_version="3.13")
# 检查关键依赖库版本
check_dependencies_version(
    requirements_file="./requirements.txt",
)

app = dash.Dash(
    __name__,
    update_title=None,
    suppress_callback_exceptions=True,
    title="A Basic Tool",
    compress=True,  # 隐式依赖flask-compress
)

app.layout = fuc.FefferyTopProgress(
    fac.AntdCenter(
        [
            # 全局消息提示
            fac.Fragment(id="global-message"),
            # 主面板
            fuc.FefferyDiv(
                [
                    fac.AntdSpace(
                        [
                            # 工具标题
                            fac.AntdText(
                                "基础工具标题",
                                style=style(
                                    fontSize=25,
                                    borderLeft="5px solid #1677ff",
                                    paddingLeft=8,
                                ),
                            ),
                            # 工具说明
                            fac.AntdText(
                                "这里是该工具的操作说明" + "巴拉" * 20,
                                type="secondary",
                            ),
                        ],
                        direction="vertical",
                        size=0,
                    ),
                    fac.AntdDivider(),
                    # 工具输入
                    fac.AntdRow(
                        [
                            # 作为State的工具输入参数
                            *[
                                fac.AntdCol(
                                    fac.AntdFormItem(
                                        fac.AntdInput(
                                            # 示例组件id，实际使用请结合实际情况编写
                                            id=f"demo-input{i}",
                                            placeholder="请输入",
                                        ),
                                        label=f"输入项{i}",
                                        layout="vertical",
                                        style=style(margin=0),
                                    ),
                                    span=6,
                                )
                                for i in range(1, 5)
                            ],
                            # 作为Input的工具输入参数提交按钮
                            fac.AntdCol(
                                fac.AntdButton(
                                    "执行计算",
                                    id="submit-button",
                                    type="primary",
                                    block=True,
                                    loadingChildren="计算中",
                                ),
                                span=24,
                            ),
                        ],
                        gutter=[5, 8],
                    ),
                    fac.AntdDivider(),
                    # 结果展示区
                    fac.AntdSpin(
                        html.Div(
                            # 初始化提示内容
                            fac.AntdCenter(
                                fac.AntdResult(
                                    subTitle="请先完善各参数后，点击按钮执行运算",
                                ),
                                style=style(paddingTop=50),
                            ),
                            id="result-container",
                        ),
                        text="拼命计算中...",
                        size="large",
                        listenPropsMode="include",
                        includeProps=[
                            "result-container.children",
                        ],
                    ),
                ],
                # 主面板基础样式
                style=style(
                    border="1px solid #dedede",
                    borderRadius=20,
                    backgroundColor="#fff",
                    width="90vw",
                    boxShadow="50px 50px 100px 10px rgba(0,0,0,.1)",
                    minWidth=600,
                    maxWidth=1200,
                    minHeight="calc(100vh - 120px)",
                    boxSizing="border-box",
                    padding="35px 28px",
                ),
            ),
        ],
        # 根容器基础样式
        style=style(
            backgroundColor="#fafafa",
            paddingTop=60,
            paddingBottom=60,
        ),
    ),
    listenPropsMode="include",
    includeProps=[
        "result-container.children",
    ],
    minimum=0.4,
)


# 相关示例回调函数


@app.callback(
    Output("result-container", "children"),
    Input("submit-button", "nClicks"),
    [
        State("demo-input1", "value"),
        State("demo-input2", "value"),
        State("demo-input3", "value"),
        State("demo-input4", "value"),
    ],
    running=[(Output("submit-button", "loading"), True, False)],
    prevent_initial_call=True,
)
def update_result(nClicks, value1, value2, value3, value4):
    """处理工具计算结果的更新输出"""

    # 模拟输入值不完善时的处理逻辑
    if not all([value1, value2, value3, value4]):
        # 额外消息提示
        set_props(
            "global-message",
            {"children": fac.AntdMessage(content="本次任务计算失败", type="error")},
        )

        return fac.AntdCenter(
            fac.AntdResult(
                title="计算失败",
                subTitle="请先完善本工具所需各项输入值",
                status="error",
            ),
            style=style(paddingTop=50),
        )

    # 模拟计算耗时，实际使用时请删除
    import time

    time.sleep(2)

    # 额外消息提示
    set_props(
        "global-message",
        {"children": fac.AntdMessage(content="本次任务计算完成", type="success")},
    )

    # 模拟计算结果返回
    return fac.AntdCenter(
        fac.AntdResult(
            title="计算完成",
            subTitle="计算结果示例",
            status="success",
        ),
        style=style(paddingTop=50),
    )


if __name__ == "__main__":
    app.run(debug=True)
