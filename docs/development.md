# 二次开发介绍

本文说明如何在 `magic-dash` 仓库本身进行开发，以及如何基于生成后的模板继续开发业务应用。

## 开发 `magic-dash` 工具本身

### 本地安装

在仓库根目录执行：

```bash
pip install -e .
```

安装后会得到 `magic-dash` 命令。

### 运行测试

```bash
pytest
```

当前测试集中在：

- `magic-dash --version`
- `magic-dash --help`
- `magic-dash list`
- `magic-dash create`
- `magic-dash-pro` 的 `Flask` 与 `FastAPI` 后端选择
- 非法模板名处理
- 目标项目名冲突处理

### 修改命令行行为

命令行入口位于 `magic_dash/__init__.py`。主要结构：

- `BUILTIN_TEMPLATES`：顶层模板列表。
- `PRO_BACKEND_TEMPLATES`：`magic-dash-pro` 后端选择到实际模板目录的映射。
- `magic_dash()`：命令组。
- `_list()`：模板列表命令。
- `_create()`：项目生成命令。

新增顶层模板时，通常需要：

1. 在 `magic_dash/templates/` 下新增模板目录。
2. 在 `BUILTIN_TEMPLATES` 中登记模板名和描述。
3. 确保模板目录包含必要入口和 `requirements.txt`。
4. 补充文档和测试。

### 模板打包

`MANIFEST.in` 使用 `graft magic_dash` 将模板和静态资源打入包内，并排除模板中不应发布的数据库文件。

## 基于 `simple-tool` 二次开发

`simple-tool` 的改造集中在 `app.py`：

1. 修改页面标题和说明。
2. 调整输入组件。
3. 替换示例计算逻辑。
4. 修改结果展示区域。
5. 新增必要依赖到 `requirements.txt`。

当单文件开始难以维护时，可以逐步拆分：

```text
components/
callbacks/
utils/
```

如果项目自然演化为多页面应用，建议迁移到 [`magic-dash`](./magic-dash.md) 的组织方式。

## 基于 `magic-dash` 二次开发

### 新增普通页面

1. 在 `views/core_pages/` 下新增页面文件，例如 `report.py`。
2. 在该文件中实现 `render()` 函数。
3. 在 `components/page_content.py` 中导入并分发该页面。
4. 在 `configs/router_config.py` 的 `valid_pathnames` 中登记路径和标题。
5. 在 `configs/router_config.py` 的 `core_side_menu` 中新增菜单项。
6. 如果页面有回调，在 `callbacks/core_pages_c/` 中新增回调模块，并在对应 `__init__.py` 中导入。

示例路径：

```python
valid_pathnames = {
    "/core/report": "报表页",
}
```

### 新增独立页面

独立页面适合大屏、打印页、嵌入页。

1. 在 `views/core_pages/` 下新增页面模块。
2. 在 `RouterConfig.valid_pathnames` 中登记路径。
3. 在 `RouterConfig.independent_core_pathnames` 中加入该路径。
4. 在 `views/core_pages/__init__.py` 的独立渲染逻辑中返回对应页面。

### 新增通配页面

通配页面适合详情页和动态参数页。

1. 在 `RouterConfig.wildcard_patterns` 中新增正则规则。
2. 将该正则对象加入 `RouterConfig.valid_pathnames`。
3. 在渲染函数中接收当前 `pathname`。
4. 从 `pathname` 中解析业务参数。

示例：

```python
wildcard_patterns = {
    "订单详情": re.compile(r"^/core/order/(.*?)$")
}
```

### 新增浏览器端回调

浏览器端回调可以放在 `assets/js/basic_callbacks.js` 或新增 `assets/js/` 下的其他文件。适合处理全屏切换、页面刷新、本地状态等前端侧能力。

## 基于 `magic-dash-pro` 二次开发

`magic-dash-pro` 的页面扩展方式与 `magic-dash` 基本一致，但需要额外维护权限、模型和登录态。

### 新增受权限控制的页面

1. 新增页面模块。
2. 接入 `components/page_content.py`。
3. 更新 `RouterConfig.valid_pathnames`。
4. 更新 `RouterConfig.core_side_menu`。
5. 更新 `AuthConfig.pathname_access_rules`。
6. 新增回调模块并导入。

### 新增角色

1. 在 `AuthConfig.roles` 中新增角色。
2. 在 `AuthConfig.pathname_access_rules` 中定义访问规则。
3. 在用户管理页面或初始化脚本中为用户分配新角色。

示例：

```python
roles = {
    "admin": {"description": "系统管理员"},
    "analyst": {"description": "分析师"},
}

pathname_access_rules = {
    "analyst": {
        "type": "include",
        "keys": ["/core/report"],
    }
}
```

### 新增数据库模型

1. 在 `models/` 下新增模型文件。
2. 继承项目中的基础模型。
3. 封装常用查询、创建、更新、删除方法。
4. 在初始化流程中创建新表。
5. 在页面回调中通过模型方法读写数据。

避免在回调函数中散落原始 `SQL` 或底层连接细节，这会让页面逻辑难以测试和维护。

### 切换数据库

修改 `configs/database_config.py`：

```python
database_type = "postgresql"
```

或：

```python
database_type = "mysql"
```

然后安装驱动并重新初始化：

```bash
pip install psycopg2-binary
python -m magic_init
```

或：

```bash
pip install pymysql
python -m magic_init
```

### 修改登录页

登录页结构位于 `views/login.py`，登录逻辑位于 `callbacks/login_c.py`。

常见修改：

- 替换登录页品牌文案。
- 切换左侧内容为图片或视频。
- 启用登录滑块验证。
- 修改登录失败提示。
- 接入外部用户系统。

### 登录安全相关修改

相关配置集中在 `BaseConfig`：

- `app_secret_key`
- `app_session_cookie_name`
- `session_token_cookie_name`
- `rsa_public_key_path`
- `rsa_private_key_path`
- `enable_duplicate_login_check`
- `enable_login_captcha`

生产环境应替换演示密钥，妥善保存 `RSA` 私钥，并根据部署域名调整 `cookie` 策略。

## 同时维护两个 Pro 后端

如果你修改的是 `magic-dash-pro` 通用页面、组件、模型或配置，通常需要同时检查：

```text
magic_dash/templates/magic-dash-pro/
magic_dash/templates/magic-dash-pro-fastapi/
```

两个目录应尽量保持业务页面和配置结构一致。差异主要集中在：

- `server.py`
- 登录态写入方式
- 当前用户和请求对象来源
- `requirements.txt`
- `BaseConfig` 中与登录有效期相关的参数
