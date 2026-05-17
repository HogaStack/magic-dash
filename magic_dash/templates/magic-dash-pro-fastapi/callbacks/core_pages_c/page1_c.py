from dash.dependencies import Input, Output

from server import app


@app.callback(
    Output("core-page1-demo-output", "children"),
    Input("core-page1-demo-button", "nClicks"),
    prevent_initial_call=True,
)
def page1_callback_demo(nClicks):
    """主要页面1演示示例回调函数"""

    return f"累计点击次数：{nClicks}"
