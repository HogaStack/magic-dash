"""FastAPI接口文档路由配置工具模块

复用Dash内置FastAPI实例，根据模板配置重新注册Swagger UI和ReDoc。
在线模式沿用FastAPI原生处理函数，离线模式复用FastAPI官方HTML生成函数，
并通过Dash的assets机制加载模板内置静态资源。
"""

from pathlib import Path
from typing import Callable, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse
from starlette.routing import Match

from configs import BaseConfig


# FastAPI内置文档路由名称
DOCUMENTATION_ROUTE_NAMES = {
    "swagger_ui_html",
    "swagger_ui_redirect",
    "redoc_html",
}

# 模板内置文档静态资源
LOCAL_DOCS_ASSET_DIRECTORY = (
    Path(__file__).resolve().parents[1] / "assets" / "fastapi-docs"
)
LOCAL_DOCS_ASSET_PATHS = {
    "swagger_js": "fastapi-docs/swagger-ui-bundle.js",
    "swagger_css": "fastapi-docs/swagger-ui.css",
    "redoc_js": "fastapi-docs/redoc.standalone.js",
    "favicon": "fastapi-docs/favicon.png",
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


def _get_local_documentation_endpoints(
    server: FastAPI,
    asset_url_builder: Optional[Callable[[str], str]],
    docs_pathname: Optional[str],
    redoc_pathname: Optional[str],
) -> Dict[str, Callable]:
    """创建使用模板内置静态资源的接口文档处理函数"""

    if not BaseConfig.fastapi_docs_offline or not (docs_pathname or redoc_pathname):
        return {}
    if not callable(asset_url_builder):
        raise ValueError("启用FastAPI离线接口文档时必须提供静态资源URL生成函数")

    required_assets = [LOCAL_DOCS_ASSET_PATHS["favicon"]]
    if docs_pathname:
        required_assets.extend(
            [
                LOCAL_DOCS_ASSET_PATHS["swagger_js"],
                LOCAL_DOCS_ASSET_PATHS["swagger_css"],
            ]
        )
    if redoc_pathname:
        required_assets.append(LOCAL_DOCS_ASSET_PATHS["redoc_js"])

    missing_assets = []
    for asset_path in required_assets:
        relative_path = Path(asset_path)
        if relative_path.parts[0] == "fastapi-docs":
            file_path = LOCAL_DOCS_ASSET_DIRECTORY.joinpath(*relative_path.parts[1:])
        else:
            file_path = LOCAL_DOCS_ASSET_DIRECTORY.parent / relative_path
        if not file_path.is_file():
            missing_assets.append(str(file_path))
    if missing_assets:
        raise FileNotFoundError(
            "FastAPI离线接口文档缺少静态资源：" + "、".join(missing_assets)
        )

    endpoints = {}

    if docs_pathname:

        async def swagger_ui_html(request: Request) -> HTMLResponse:
            root_path = request.scope.get("root_path", "").rstrip("/")
            oauth2_redirect_url = server.swagger_ui_oauth2_redirect_url
            if oauth2_redirect_url:
                oauth2_redirect_url = root_path + oauth2_redirect_url

            return get_swagger_ui_html(
                openapi_url=root_path + server.openapi_url,
                title=f"{server.title} - Swagger UI",
                swagger_js_url=asset_url_builder(LOCAL_DOCS_ASSET_PATHS["swagger_js"]),
                swagger_css_url=asset_url_builder(
                    LOCAL_DOCS_ASSET_PATHS["swagger_css"]
                ),
                swagger_favicon_url=asset_url_builder(
                    LOCAL_DOCS_ASSET_PATHS["favicon"]
                ),
                oauth2_redirect_url=oauth2_redirect_url,
                init_oauth=server.swagger_ui_init_oauth,
                swagger_ui_parameters=server.swagger_ui_parameters,
            )

        endpoints["swagger_ui_html"] = swagger_ui_html

    if redoc_pathname:

        async def redoc_html(request: Request) -> HTMLResponse:
            root_path = request.scope.get("root_path", "").rstrip("/")
            return get_redoc_html(
                openapi_url=root_path + server.openapi_url,
                title=f"{server.title} - ReDoc",
                redoc_js_url=asset_url_builder(LOCAL_DOCS_ASSET_PATHS["redoc_js"]),
                redoc_favicon_url=asset_url_builder(LOCAL_DOCS_ASSET_PATHS["favicon"]),
                with_google_fonts=False,
            )

        endpoints["redoc_html"] = redoc_html

    return endpoints


def configure_fastapi_documentation(
    server: FastAPI,
    asset_url_builder: Optional[Callable[[str], str]] = None,
) -> None:
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
    documentation_endpoints.update(
        _get_local_documentation_endpoints(
            server,
            asset_url_builder,
            docs_pathname,
            redoc_pathname,
        )
    )

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
