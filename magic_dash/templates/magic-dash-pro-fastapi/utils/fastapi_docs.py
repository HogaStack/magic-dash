"""FastAPI接口文档路由配置工具模块

复用Dash内置FastAPI实例已经创建的文档处理函数，根据模板配置重新注册
Swagger UI和ReDoc，不额外创建FastAPI实例或重复实现文档页面。
"""

from typing import Optional

from fastapi import FastAPI
from starlette.routing import Match

from configs import BaseConfig


# FastAPI内置文档路由名称
DOCUMENTATION_ROUTE_NAMES = {
    "swagger_ui_html",
    "swagger_ui_redirect",
    "redoc_html",
}


def is_fastapi_documentation_pathname(server: FastAPI, pathname: str) -> bool:
    """判断pathname是否为OpenAPI定义或已启用的接口文档路由"""

    return pathname in {
        server.openapi_url,
        server.docs_url,
        server.redoc_url,
        server.swagger_ui_oauth2_redirect_url,
    }


def _get_pathname(enabled: bool, config_name: str) -> Optional[str]:
    """读取并校验已启用的接口文档pathname配置"""

    if not enabled:
        return None

    pathname = getattr(BaseConfig, config_name)
    if (
        not isinstance(pathname, str)
        or not pathname.startswith("/")
        or pathname.startswith("//")
    ):
        raise ValueError(f"BaseConfig.{config_name}必须是以'/'开头的字符串")
    if pathname == "/":
        raise ValueError(f"BaseConfig.{config_name}不能占用应用根路径'/'")
    if any(character in pathname for character in ["?", "#", "{", "}"]):
        raise ValueError(
            f"BaseConfig.{config_name}必须是静态pathname，不能包含查询参数、锚点或路径参数"
        )

    return pathname.rstrip("/")


def _ensure_pathname_available(
    server: FastAPI,
    pathname: str,
    config_name: str,
) -> None:
    """校验接口文档pathname是否已被现有业务路由占用"""

    scope = {
        "type": "http",
        "path": pathname,
        "method": "GET",
        "root_path": "",
    }
    if any(
        getattr(route, "name", None) not in DOCUMENTATION_ROUTE_NAMES
        and route.matches(scope)[0] == Match.FULL
        for route in server.routes
    ):
        raise ValueError(f"BaseConfig.{config_name}配置的{pathname!r}已被现有路由占用")


def configure_fastapi_documentation(server: FastAPI) -> None:
    """根据BaseConfig重新注册当前FastAPI实例的接口文档路由"""

    docs_pathname = _get_pathname(
        BaseConfig.enable_fastapi_docs,
        "fastapi_docs_pathname",
    )
    redoc_pathname = _get_pathname(
        BaseConfig.enable_fastapi_redoc,
        "fastapi_redoc_pathname",
    )

    if docs_pathname and docs_pathname == redoc_pathname:
        raise ValueError(
            "BaseConfig.fastapi_docs_pathname和"
            "BaseConfig.fastapi_redoc_pathname不能配置为相同地址"
        )
    if (docs_pathname or redoc_pathname) and not server.openapi_url:
        raise ValueError("启用FastAPI接口文档时server.openapi_url不能为空")

    route_configs = {
        "swagger_ui_html": (docs_pathname, "fastapi_docs_pathname"),
        "swagger_ui_redirect": (
            f"{docs_pathname}/oauth2-redirect" if docs_pathname else None,
            "fastapi_docs_pathname",
        ),
        "redoc_html": (redoc_pathname, "fastapi_redoc_pathname"),
    }
    documentation_endpoints = {
        route.name: route.endpoint
        for route in server.routes
        if getattr(route, "name", None) in DOCUMENTATION_ROUTE_NAMES
    }

    # 所有检查完成后再修改路由，避免配置异常导致服务实例处于不完整状态
    for route_name, (pathname, config_name) in route_configs.items():
        if not pathname:
            continue
        if route_name not in documentation_endpoints:
            raise RuntimeError("当前FastAPI实例缺少内置接口文档路由")
        _ensure_pathname_available(server, pathname, config_name)

    server.router.routes[:] = [
        route
        for route in server.routes
        if getattr(route, "name", None) not in DOCUMENTATION_ROUTE_NAMES
    ]
    server.title = BaseConfig.app_title
    server.version = BaseConfig.app_version
    server.docs_url = docs_pathname
    server.redoc_url = redoc_pathname
    server.swagger_ui_oauth2_redirect_url = route_configs["swagger_ui_redirect"][0]

    for route_name, (pathname, _) in route_configs.items():
        if pathname:
            server.add_route(
                pathname,
                documentation_endpoints[route_name],
                name=route_name,
                include_in_schema=False,
            )
