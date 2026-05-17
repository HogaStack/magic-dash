import os

from dash import dcc
import feffery_antd_components as fac
import feffery_markdown_components as fmc
from dash.dependencies import Input, Output

from server import app
from configs.base_config import BaseConfig


def render():
    """渲染版本更新日志通知"""

    if BaseConfig.enable_version_changelog_modal:
        return fac.Fragment(
            [
                # 最近一次已读版本标识
                dcc.Store(
                    id="core-page-version-changelog-viewed-version",
                    storage_type="local",
                ),
                # 当前版本更新内容模态框
                fac.AntdModal(
                    fmc.FefferyMarkdown(
                        markdownStr=open(
                            os.path.join(
                                BaseConfig.version_changelog_markdown_folder,
                                "{}.md".format(BaseConfig.app_version),
                            ),
                            encoding="utf-8",
                        ).read(),
                    ),
                    id="core-page-version-changelog-modal",
                    title="{}版本更新内容".format(BaseConfig.app_version),
                    renderFooter=True,
                    cancelButtonProps={"style": {"display": "none"}},
                    okText="已阅",
                ),
            ]
        )


@app.callback(
    Output("core-page-version-changelog-modal", "visible"),
    Input("core-page-version-changelog-viewed-version", "data"),
)
def handle_version_changelog_visible(version):
    """判断是否显示版本更新内容通知"""
    if version != BaseConfig.app_version:
        return True


@app.callback(
    Output("core-page-version-changelog-viewed-version", "data"),
    Input("core-page-version-changelog-modal", "okCounts"),
    prevent_initial_call=True,
)
def update_version_changelog_viewed_version(okCounts):
    """在用户点击“已阅”后，更新最近一次已读版本标识"""
    return BaseConfig.app_version
