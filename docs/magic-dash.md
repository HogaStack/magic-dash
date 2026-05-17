# `magic-dash` 模板介绍

`magic-dash` 是基础多页面 [`Dash`](https://github.com/plotly/dash) 应用模板，用于快速搭建带侧边菜单、统一页面框架、路由分发、状态页和可扩展配置的后台应用雏形。

## 适用场景

优先选择 `magic-dash` 的典型情况：

- 需要多个业务页面。
- 需要统一的侧边菜单和主内容区。
- 需要维护页面路由、页面标题、菜单展开状态。
- 需要独立页面，例如大屏页、打印页、嵌入页。
- 需要动态路径或详情页，例如 `/core/order/123`。
- 暂时不需要登录、角色权限和数据库模型。

如果项目需要用户体系、权限和后台管理能力，应选择 [`magic-dash-pro`](./magic-dash-pro.md)。

## 创建方式

```bash
magic-dash create --name magic-dash
```

指定生成目录：

```bash
magic-dash create --name magic-dash --path ./workspace
```

## 启动方式

```bash
cd magic-dash
pip install -r requirements.txt
python app.py
```

默认访问地址：

```text
http://127.0.0.1:8050
```

## 目录结构

```text
magic-dash/
├─ assets/
│  ├─ css/
│  ├─ imgs/
│  ├─ js/
│  └─ favicon.ico
├─ callbacks/
│  └─ core_pages_c/
├─ components/
├─ configs/
│  ├─ base_config.py
│  ├─ layout_config.py
│  └─ router_config.py
├─ utils/
├─ views/
│  ├─ core_pages/
│  └─ status_pages/
├─ server.py
├─ app.py
└─ requirements.txt
```

## 核心模块

| 文件或目录 | 职责 |
| --- | --- |
| `app.py` | 应用入口、根布局、根路由回调、状态页分发 |
| `server.py` | 创建 `Dash` 应用实例，暴露 `server`，执行浏览器版本拦截 |
| `configs/base_config.py` | 应用标题、版本、浏览器版本、更新日志弹窗配置 |
| `configs/layout_config.py` | 侧边栏宽度、页面呈现类型、页面搜索配置 |
| `configs/router_config.py` | 路由、菜单、独立页面、通配页面配置 |
| `components/core_side_menu.py` | 侧边菜单渲染 |
| `components/page_content.py` | 页面内容分发 |
| `views/core_pages/` | 核心业务页面 |
| `views/status_pages/` | `404`、`500` 状态页 |
| `callbacks/core_pages_c/` | 业务页面回调模块 |
| `assets/js/basic_callbacks.js` | 浏览器端回调函数 |

## 路由机制

模板使用 `FefferyLocation` 监听浏览器地址变化，根回调会根据当前 `pathname` 执行以下逻辑：

1. 如果访问 `/404-demo` 或 `/500-demo`，渲染对应状态页。
2. 如果 `pathname` 存在于 `RouterConfig.valid_pathnames`，渲染核心页面。
3. 如果 `pathname` 命中 `RouterConfig.valid_pathnames` 中的正则通配规则，渲染通配页面。
4. 其他情况返回 `404` 页面。

核心页面再由 `views/core_pages/__init__.py` 判断是否需要完整框架渲染或独立渲染。

## 页面类型

### 普通核心页面

普通核心页面会进入统一应用框架，通常带侧边栏、页首、页面搜索和主内容区。适合绝大多数后台业务页。

相关配置：

- `RouterConfig.valid_pathnames`
- `RouterConfig.core_side_menu`
- `components/page_content.py`
- `views/core_pages/`

### 独立页面

独立页面会跳过核心框架，直接渲染页面内容。适合大屏、报表打印、第三方嵌入等场景。

相关配置：

- `RouterConfig.independent_core_pathnames`
- `views/core_pages/__init__.py`

### 通配页面

通配页面基于 `re.Pattern` 匹配动态路径，适合详情页和参数化页面。

相关配置：

- `RouterConfig.wildcard_patterns`
- `RouterConfig.valid_pathnames`
- `RouterConfig.independent_core_pathnames`

## 布局能力

`LayoutConfig.core_layout_type` 支持两种核心内容区呈现方式：

- `single`：单页面模式，路由切换时替换主内容区。
- `tabs`：多标签页模式，适合需要同时打开多个业务页面的后台应用。

`LayoutConfig.show_core_page_search` 控制页首页面搜索框是否展示。

## 内置示例页面

模板包含以下示例页面，用于展示常见能力：

- 首页。
- 普通核心页面。
- 多级子菜单页面。
- 独立页面入口和独立页面示例。
- 独立通配页面入口和动态路径示例。
- `URL` 参数提取示例。
- `404` 和 `500` 状态页。

## 浏览器版本检查

`server.py` 会在请求进入应用前解析 `User-Agent`，基于 `BaseConfig.min_browser_versions` 拦截低版本浏览器，并默认直接拦截 `Internet Explorer`。

可通过 `BaseConfig.strict_browser_type_check` 控制是否只允许配置表中声明的浏览器类型。

## 进一步阅读

- [配置参数说明](./configuration.md)
- [二次开发介绍](./development.md)
- [`magic-dash` 命令使用](./cli.md)
