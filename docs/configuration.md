# 配置参数说明

`magic-dash` 系列模板把应用配置集中放在 `configs/` 目录中。配置文件均为普通 `Python` 类属性，生成项目后可以直接修改。

`simple-tool` 模板刻意保持单文件结构，没有独立 `configs/` 目录。以下内容主要适用于 [`magic-dash`](./magic-dash.md) 和 [`magic-dash-pro`](./magic-dash-pro.md)。

## 配置文件总览

| 文件 | 适用模板 | 职责 |
| --- | --- | --- |
| `configs/base_config.py` | `magic-dash`、`magic-dash-pro` | 应用标题、版本、浏览器限制、更新日志、安全相关基础配置 |
| `configs/layout_config.py` | `magic-dash`、`magic-dash-pro` | 侧边栏、内容区、页面搜索、登录页布局配置 |
| `configs/router_config.py` | `magic-dash`、`magic-dash-pro` | 菜单、路由、有效页面、独立页面、通配页面配置 |
| `configs/auth_config.py` | `magic-dash-pro` | 角色定义和页面访问规则 |
| `configs/database_config.py` | `magic-dash-pro` | 数据库类型和连接信息 |

## `BaseConfig`

### 通用参数

| 参数 | 默认值 | 适用模板 | 说明 |
| --- | --- | --- | --- |
| `app_title` | `Magic Dash` 或 `Magic Dash Pro` | 全部多页面模板 | 应用标题，同时影响浏览器标题和页面展示 |
| `app_version` | `dev`，生成后替换为当前 `magic-dash` 版本 | 全部多页面模板 | 应用版本号 |
| `enable_version_changelog_modal` | `False` | 全部多页面模板 | 是否启用版本更新日志弹窗 |
| `version_changelog_markdown_folder` | `changelogs` | 全部多页面模板 | 更新日志 `Markdown` 文件目录 |
| `min_browser_versions` | `Chrome 88`、`Firefox 78`、`Edge 100` | 全部多页面模板 | 浏览器最低版本规则 |
| `strict_browser_type_check` | `False` | 全部多页面模板 | 是否只允许规则中声明的浏览器类型 |

### `magic-dash-pro` 安全参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `app_secret_key` | 模板内置演示密钥 | 应用密钥；生产环境必须替换 |
| `app_session_cookie_name` | `magic_dash_pro_session` | 登录会话 `cookie` 名称 |
| `enable_duplicate_login_check` | `False` | 是否启用重复登录检测 |
| `duplicate_login_check_interval` | `10` | 重复登录检测轮询间隔，单位为秒 |
| `session_token_cookie_name` | `session_token` | 重复登录检测使用的会话令牌 `cookie` 名称 |
| `enable_fullscreen_watermark` | `False` | 是否启用全屏水印 |
| `fullscreen_watermark_generator` | 当前用户名 | 水印内容生成函数 |
| `rsa_public_key_path` | `magic_dash_pro_public_key.pem` | 登录密码加密传输使用的 `RSA` 公钥路径 |
| `rsa_private_key_path` | `magic_dash_pro_private_key.pem` | 登录密码加密传输使用的 `RSA` 私钥路径 |
| `enable_login_captcha` | `False` | 是否启用登录页滑块验证 |

### `FastAPI` 后端额外参数

仅 [`magic-dash-pro` FastAPI 后端](./magic-dash-pro-fastapi.md) 包含：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `login_session_expire_seconds` | `12 * 60 * 60` | 未勾选“记住我”时的登录有效期 |
| `remember_login_expire_seconds` | `30 * 24 * 60 * 60` | 勾选“记住我”后的登录有效期 |

## `LayoutConfig`

| 参数 | 默认值 | 适用模板 | 说明 |
| --- | --- | --- | --- |
| `core_side_width` | `350` | 全部多页面模板 | 核心页面侧边栏宽度，单位为像素 |
| `core_layout_type` | `single` | 全部多页面模板 | 核心内容呈现方式，可选 `single`、`tabs` |
| `show_core_page_search` | `True` | 全部多页面模板 | 是否在页首展示页面搜索框 |
| `login_left_side_content_type` | `image` | `magic-dash-pro` | 登录页左侧内容类型，可选 `image`、`video` |

## `RouterConfig`

| 参数 | 适用模板 | 说明 |
| --- | --- | --- |
| `index_pathname` | 全部多页面模板 | 首页路径别名，默认 `/index` |
| `core_side_menu` | 全部多页面模板 | 侧边菜单结构 |
| `wildcard_patterns` | 全部多页面模板 | 通配页面正则规则 |
| `valid_pathnames` | 全部多页面模板 | 有效路径与页面标题映射 |
| `independent_core_pathnames` | 全部多页面模板 | 跳过核心框架、独立渲染的页面路径 |
| `side_menu_open_keys` | 全部多页面模板 | 访问指定路径时自动展开的菜单层级 |
| `public_pathnames` | `magic-dash-pro` | 无需登录即可访问的公开页面 |

### 菜单结构

`core_side_menu` 使用字典描述菜单组件，常见 `component` 类型：

- `ItemGroup`：菜单分组。
- `Item`：菜单项。
- `SubMenu`：子菜单。

菜单项中的 `key` 和 `href` 建议保持一致，方便路由、权限和菜单状态联动。

### 通配页面

`wildcard_patterns` 使用 `re.compile()` 定义动态路径。例如：

```python
wildcard_patterns = {
    "订单详情": re.compile(r"^/core/order/(.*?)$")
}
```

再将该正则对象加入 `valid_pathnames`，即可被根路由识别。

## `AuthConfig`

仅 `magic-dash-pro` 包含。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `roles` | `admin`、`normal` | 系统角色定义 |
| `normal_role` | `normal` | 常规用户角色键名 |
| `admin_role` | `admin` | 管理员角色键名 |
| `pathname_access_rules` | 管理员全部可访问，常规用户排除登录日志页 | 页面访问规则 |

权限规则示例：

```python
pathname_access_rules = {
    "admin": {"type": "all"},
    "normal": {
        "type": "exclude",
        "keys": ["/core/login-logs"],
    },
}
```

规则类型：

- `all`：可访问全部有效页面。
- `include`：仅可访问 `keys` 中列出的页面，首页会自动纳入。
- `exclude`：不可访问 `keys` 中列出的页面。

## `DatabaseConfig`

仅 `magic-dash-pro` 包含。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `database_type` | `sqlite` | 数据库类型，可选 `sqlite`、`postgresql`、`mysql` |
| `postgresql_config` | 本地演示配置 | `PostgreSQL` 连接参数 |
| `mysql_config` | 本地演示配置 | `MySQL` 连接参数 |

切换到 `PostgreSQL` 时，需要安装对应驱动：

```bash
pip install psycopg2-binary
```

切换到 `MySQL` 时，需要安装对应驱动：

```bash
pip install pymysql
```

修改数据库配置后，重新执行：

```bash
python -m magic_init
```

## 配置修改建议

- 业务页面路由、菜单和权限应同步维护，避免出现页面可访问但菜单不可见，或菜单存在但权限不可达的情况。
- 生产环境必须替换 `app_secret_key`。
- 同一域名或同一主机部署多个 `magic-dash-pro` 应用时，应为每个应用设置不同的 `app_session_cookie_name` 和 `session_token_cookie_name`。
- 切换数据库类型后，应把数据库驱动写入 `requirements.txt`。
- 修改 `core_layout_type` 为 `tabs` 后，应重点测试页面切换、刷新和回调状态。
