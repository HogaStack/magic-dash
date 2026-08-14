import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


TEMPLATE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "magic_dash"
    / "templates"
    / "magic-dash-pro-fastapi"
)


def clear_template_modules():
    """清理模板使用的顶层模块，避免不同测试之间共享配置。"""

    for module_name in list(sys.modules):
        if module_name == "server":
            sys.modules.pop(module_name)
        elif module_name == "models" or module_name.startswith("models."):
            sys.modules.pop(module_name)
        elif module_name == "configs" or module_name.startswith("configs."):
            sys.modules.pop(module_name)
        elif module_name == "utils" or module_name.startswith("utils."):
            sys.modules.pop(module_name)


@pytest.fixture
def fastapi_docs_utils(monkeypatch):
    pytest.importorskip("fastapi")

    clear_template_modules()
    monkeypatch.syspath_prepend(str(TEMPLATE_ROOT))
    module = importlib.import_module("utils.fastapi_docs")

    yield module

    clear_template_modules()


@pytest.fixture
def template_server_factory(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("fastapi_login")
    pytest.importorskip("peewee")
    pytest.importorskip("user_agents")

    def load_template_server(**config_values):
        clear_template_modules()
        monkeypatch.chdir(tmp_path)
        monkeypatch.syspath_prepend(str(TEMPLATE_ROOT))

        configs = importlib.import_module("configs")
        for config_name, config_value in config_values.items():
            monkeypatch.setattr(configs.BaseConfig, config_name, config_value)

        return importlib.import_module("server")

    yield load_template_server

    clear_template_modules()


@pytest.fixture
def template_server(template_server_factory):
    return template_server_factory()


def configure_documentation(
    fastapi_docs_utils,
    server,
    monkeypatch,
    *,
    enable_docs=False,
    docs_pathname="/docs",
    enable_redoc=False,
    redoc_pathname="/redoc",
):
    """使用测试配置调用接口文档注册函数。"""

    config_values = {
        "enable_fastapi_docs": enable_docs,
        "fastapi_docs_pathname": docs_pathname,
        "enable_fastapi_redoc": enable_redoc,
        "fastapi_redoc_pathname": redoc_pathname,
        "app_title": "测试应用",
        "app_version": "test",
    }
    for config_name, config_value in config_values.items():
        monkeypatch.setattr(
            fastapi_docs_utils.BaseConfig,
            config_name,
            config_value,
        )

    fastapi_docs_utils.configure_fastapi_documentation(server)


def get_documentation_routes(server):
    """提取指定FastAPI实例中的接口文档路由。"""

    documentation_route_names = {
        "swagger_ui_html",
        "swagger_ui_redirect",
        "redoc_html",
    }
    return [
        route
        for route in server.routes
        if getattr(route, "name", None) in documentation_route_names
    ]


def get_authenticated_client(template_server, monkeypatch, user_role):
    """创建具有指定用户角色登录cookie的模板测试客户端。"""

    from fastapi.testclient import TestClient

    user_id = f"{user_role}-user"
    user = SimpleNamespace(
        user_id=user_id,
        user_name=user_id,
        user_role=user_role,
        session_token="test-session-token",
    )
    monkeypatch.setattr(
        template_server.Users,
        "get_user",
        staticmethod(lambda match_user_id: user if match_user_id == user_id else None),
    )

    access_token = template_server.manager.create_access_token(
        data={"sub": user_id},
    )
    client = TestClient(template_server.server)
    client.cookies.set(
        template_server.BaseConfig.app_session_cookie_name,
        access_token,
    )

    return client


def test_template_disables_fastapi_documentation_by_default(template_server):
    from fastapi.testclient import TestClient

    assert not template_server.BaseConfig.enable_fastapi_docs
    assert template_server.BaseConfig.fastapi_docs_pathname == "/docs"
    assert not template_server.BaseConfig.enable_fastapi_redoc
    assert template_server.BaseConfig.fastapi_redoc_pathname == "/redoc"
    assert template_server.BaseConfig.fastapi_docs_admin_only
    assert template_server.server.docs_url is None
    assert template_server.server.redoc_url is None
    assert get_documentation_routes(template_server.server) == []

    openapi_response = TestClient(template_server.server).get("/openapi.json")

    assert openapi_response.status_code == 401
    assert openapi_response.json() == {
        "detail": "登录后才能访问FastAPI接口文档"
    }


def test_admin_only_documentation_rejects_anonymous_user(template_server_factory):
    from fastapi.testclient import TestClient

    template_server = template_server_factory(
        enable_fastapi_docs=True,
        fastapi_docs_pathname="/api-docs",
        enable_fastapi_redoc=True,
        fastapi_redoc_pathname="/api-redoc",
    )
    client = TestClient(template_server.server)

    for pathname in [
        "/api-docs",
        "/api-docs/oauth2-redirect",
        "/api-redoc",
        "/openapi.json",
    ]:
        response = client.get(pathname)
        assert response.status_code == 401
        assert response.json() == {
            "detail": "登录后才能访问FastAPI接口文档"
        }


def test_admin_only_documentation_rejects_non_admin_user(
    template_server_factory,
    monkeypatch,
):
    template_server = template_server_factory(
        enable_fastapi_docs=True,
        enable_fastapi_redoc=True,
    )
    client = get_authenticated_client(
        template_server,
        monkeypatch,
        template_server.AuthConfig.normal_role,
    )

    for pathname in ["/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"]:
        response = client.get(pathname)
        assert response.status_code == 403
        assert response.json() == {
            "detail": "仅管理员可以访问FastAPI接口文档"
        }


def test_admin_only_documentation_allows_admin_user(
    template_server_factory,
    monkeypatch,
):
    template_server = template_server_factory(
        enable_fastapi_docs=True,
        enable_fastapi_redoc=True,
    )
    client = get_authenticated_client(
        template_server,
        monkeypatch,
        template_server.AuthConfig.admin_role,
    )

    for pathname in ["/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"]:
        assert client.get(pathname).status_code == 200

    assert client.get("/openapi.json").json()["info"] == {
        "title": template_server.BaseConfig.app_title,
        "version": template_server.BaseConfig.app_version,
    }


def test_admin_only_documentation_treats_invalid_cookie_as_anonymous(
    template_server_factory,
):
    from fastapi.testclient import TestClient

    template_server = template_server_factory(enable_fastapi_docs=True)
    client = TestClient(template_server.server)
    client.cookies.set(
        template_server.BaseConfig.app_session_cookie_name,
        "invalid-access-token",
    )

    response = client.get("/docs")

    assert response.status_code == 401
    assert response.json() == {"detail": "登录后才能访问FastAPI接口文档"}


def test_admin_only_documentation_uses_current_database_role(
    template_server_factory,
    monkeypatch,
):
    from fastapi.testclient import TestClient

    template_server = template_server_factory(enable_fastapi_docs=True)
    user_id = "role-change-user"
    current_role = {"value": template_server.AuthConfig.admin_role}

    def get_user(match_user_id):
        if match_user_id != user_id:
            return None
        return SimpleNamespace(
            user_id=user_id,
            user_name=user_id,
            user_role=current_role["value"],
            session_token="test-session-token",
        )

    monkeypatch.setattr(
        template_server.Users,
        "get_user",
        staticmethod(get_user),
    )
    access_token = template_server.manager.create_access_token(data={"sub": user_id})
    client = TestClient(template_server.server)
    client.cookies.set(
        template_server.BaseConfig.app_session_cookie_name,
        access_token,
    )

    assert client.get("/docs").status_code == 200

    current_role["value"] = template_server.AuthConfig.normal_role

    assert client.get("/docs").status_code == 403


def test_documentation_can_remain_public(template_server_factory):
    from fastapi.testclient import TestClient

    template_server = template_server_factory(
        enable_fastapi_docs=True,
        enable_fastapi_redoc=True,
        fastapi_docs_admin_only=False,
    )
    client = TestClient(template_server.server)

    for pathname in ["/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"]:
        assert client.get(pathname).status_code == 200


@pytest.mark.parametrize(
    ("enable_docs", "enable_redoc"),
    [
        (False, False),
        (True, False),
        (False, True),
        (True, True),
    ],
)
def test_fastapi_documentation_switches_are_independent(
    fastapi_docs_utils,
    monkeypatch,
    enable_docs,
    enable_redoc,
):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    server = FastAPI()
    configure_documentation(
        fastapi_docs_utils,
        server,
        monkeypatch,
        enable_docs=enable_docs,
        enable_redoc=enable_redoc,
    )

    client = TestClient(server)
    assert server.docs_url == ("/docs" if enable_docs else None)
    assert server.redoc_url == ("/redoc" if enable_redoc else None)
    assert client.get("/docs").status_code == (200 if enable_docs else 404)
    assert client.get("/redoc").status_code == (200 if enable_redoc else 404)


def test_fastapi_documentation_supports_independent_pathname_aliases(
    fastapi_docs_utils,
    monkeypatch,
):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    server = FastAPI()

    @server.get("/api/health", tags=["系统"])
    async def health_check():
        return {"status": "ok"}

    original_endpoints = {
        route.name: route.endpoint for route in get_documentation_routes(server)
    }
    configure_documentation(
        fastapi_docs_utils,
        server,
        monkeypatch,
        enable_docs=True,
        docs_pathname="/api-docs/",
        enable_redoc=True,
        redoc_pathname="/api-redoc",
    )

    route_pathnames = {
        route.name: route.path for route in get_documentation_routes(server)
    }
    assert route_pathnames == {
        "swagger_ui_html": "/api-docs",
        "swagger_ui_redirect": "/api-docs/oauth2-redirect",
        "redoc_html": "/api-redoc",
    }
    assert {
        route.name: route.endpoint for route in get_documentation_routes(server)
    } == original_endpoints
    assert fastapi_docs_utils.is_fastapi_documentation_pathname(server, "/api-docs")
    assert fastapi_docs_utils.is_fastapi_documentation_pathname(server, "/api-redoc")
    assert not fastapi_docs_utils.is_fastapi_documentation_pathname(server, "/login")

    client = TestClient(server)
    docs_response = client.get("/api-docs")
    redoc_response = client.get("/api-redoc")
    oauth2_redirect_response = client.get("/api-docs/oauth2-redirect")
    health_response = client.get("/api/health")
    openapi_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert "SwaggerUIBundle" in docs_response.text
    assert "url: '/openapi.json'" in docs_response.text
    assert "cdn.jsdelivr.net/npm/swagger-ui-dist" in docs_response.text
    assert redoc_response.status_code == 200
    assert "cdn.jsdelivr.net/npm/redoc" in redoc_response.text
    assert oauth2_redirect_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert openapi_response.json()["paths"]["/api/health"]["get"]["tags"] == ["系统"]


def test_api_registered_after_documentation_is_included_in_openapi(
    fastapi_docs_utils,
    monkeypatch,
):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    server = FastAPI()
    configure_documentation(
        fastapi_docs_utils,
        server,
        monkeypatch,
        enable_docs=True,
    )

    @server.get("/api/late-registration", tags=["后注册接口"])
    async def late_registration():
        return {"status": "ok"}

    client = TestClient(server)
    assert client.get("/api/late-registration").json() == {"status": "ok"}
    assert client.get("/openapi.json").json()["paths"]["/api/late-registration"]["get"][
        "tags"
    ] == ["后注册接口"]


def test_disabled_documentation_pathname_is_not_validated(
    fastapi_docs_utils,
    monkeypatch,
):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    server = FastAPI()
    configure_documentation(
        fastapi_docs_utils,
        server,
        monkeypatch,
        docs_pathname="未启用时不参与校验",
        enable_redoc=True,
        redoc_pathname="/reference",
    )

    assert server.docs_url is None
    assert server.redoc_url == "/reference"
    assert TestClient(server).get("/reference").status_code == 200


@pytest.mark.parametrize(
    ("docs_pathname", "redoc_pathname", "error_pattern"),
    [
        ("api-docs", "/redoc", "必须是以'/'开头"),
        ("/", "/redoc", "不能占用应用根路径"),
        ("/_dash-layout", "/redoc", "已被现有路由占用"),
        ("/assets/api-docs", "/redoc", "已被现有路由占用"),
        ("/reference", "/reference", "不能配置为相同地址"),
    ],
)
def test_invalid_fastapi_documentation_pathnames_fail_fast(
    fastapi_docs_utils,
    monkeypatch,
    docs_pathname,
    redoc_pathname,
    error_pattern,
):
    from fastapi import FastAPI
    from starlette.responses import Response

    server = FastAPI()

    async def dash_layout():
        return {}

    async def assets_app(scope, receive, send):
        await Response()(scope, receive, send)

    server.add_api_route("/_dash-layout", dash_layout)
    server.mount("/assets", assets_app, name="assets")

    with pytest.raises(ValueError, match=error_pattern):
        configure_documentation(
            fastapi_docs_utils,
            server,
            monkeypatch,
            enable_docs=True,
            docs_pathname=docs_pathname,
            enable_redoc=True,
            redoc_pathname=redoc_pathname,
        )


def test_enabled_documentation_requires_openapi(fastapi_docs_utils, monkeypatch):
    from fastapi import FastAPI

    server = FastAPI(openapi_url=None)

    with pytest.raises(ValueError, match="openapi_url不能为空"):
        configure_documentation(
            fastapi_docs_utils,
            server,
            monkeypatch,
            enable_docs=True,
        )
