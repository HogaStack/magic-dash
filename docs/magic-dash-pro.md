# `magic-dash-pro`

多页面+用户登录应用模板。

## 1 创建方式

```bash
magic-dash create --name magic-dash-pro
```

## 2 应用初始化启动

- 安装项目依赖库

```bash
pip install -r requirements.txt
```

- 用户信息数据库初始化

```bash
python -m models.init_db
```

- 启动应用

```bash
python app.py
```

- 访问应用

应用默认地址：http://127.0.0.1:8050

- 自带管理员账号信息

```
用户名：admin
密码：admin123
```

## 3 项目目录结构

```bash
magic-dash-pro
 ┣ assets # 静态资源目录
 ┃ ┣ css # 样式文件目录
 ┃ ┣ imgs # 图片文件目录
 ┃ ┣ js # 浏览器回调函数目录
 ┃ ┗ favicon.ico # 网页图标
 ┣ callbacks # 回调函数模块
 ┣ components # 自定义组件模块
 ┣ configs # 配置参数模块
 ┣ models # 数据库模型模块
 ┣ utils # 工具函数模块
 ┣ views # 页面模块
 ┣ magic_dash_pro.db # 数据库文件（初始化后自动生成）
 ┣ server.py # 应用初始化模块
 ┣ app.py # 应用主文件
 ┗ requirements.txt # 项目依赖信息
```

## 4 主要功能配置说明

### 4.1 基础配置

#### 4.1.1 浏览器版本检测&限制

> `BaseConfig.min_browser_versions`

针对用户浏览器最低版本检测功能，配置所依赖的相关浏览器类型及最低版本信息，默认值：

```python
[
    {"browser": "Chrome", "version": 88},
    {"browser": "Firefox", "version": 78},
    {"browser": "Edge", "version": 100},
]
```

> `BaseConfig.strict_browser_type_check`

针对用户浏览器最低版本检测功能，配置是否开启严格的浏览器类型限制，默认值：`False`，设置为`True`后，将依据`min_browser_versions`参数，直接拦截不在所列举范围内的浏览器类型。

#### 4.1.2 应用基础标题

> `BaseConfig.app_title`

设置应用基础标题，默认值：`Magic Dash`。

#### 4.1.3 应用版本号

> `BaseConfig.app_version`

设置应用版本号。

#### 4.1.4 应用密钥

> `BaseConfig.app_secret_key`

设置应用密钥，用于配合实现用户登录相关底层逻辑。

#### 4.1.5 重复登录检测

> `BaseConfig.enable_duplicate_login_check`

设置是否开启重复登录检测功能，默认值：`False`。

> `BaseConfig.duplicate_login_check_interval`

设置重复登录检测间隔时间，单位：秒，默认值：`10`。

> `BaseConfig.session_token_cookie_name`

登录会话token对应的cookies项名称，默认值：`session_token`。

#### 4.1.6 全屏水印

> `BaseConfig.enable_fullscreen_watermark`

设置是否开启全屏额外水印功能，默认值：`False`。

> `BaseConfig.fullscreen_watermark_generator`

接受`lambda`函数或常规函数方法，用于动态处理实际水印内容输出，默认值：

```python
# 其中current_user对应flask-login中的当前用户对象
lambda current_user: current_user.user_name
```

### 4.2 布局配置

#### 4.2.1 核心页面侧边栏宽度

> `LayoutConfig.core_side_width`

设置核心页面侧边栏像素宽度，默认值：`350`。

#### 4.2.2 登录页面左侧内容

> `LayoutConfig.login_left_side_content_type`

设置登录页面左侧内容类型，默认值：`image`，可选项有`image`（图片内容）、`video`（视频内容）。

#### 4.2.3 核心页面呈现类型

> `LayoutConfig.core_layout_type`

设置核心页面呈现类型，默认值：`single`，可选项有`single`（单页面形式）、`tabs`（多标签页形式）。

#### 4.2.4 页面搜索框展示

> `LayoutConfig.show_core_page_search`

设置页首中的页面搜索框是否展示，默认值：`True`。

### 4.3 路由配置

#### 4.3.1 首页路径别名

> `RouterConfig.index_pathname`

设置首页路径别名，默认值：`/index`。

#### 4.3.2 核心页面侧边菜单结构

> `RouterConfig.core_side_menu`

核心页面侧边菜单结构。

#### 4.3.3 有效页面路径&标题映射

> `RouterConfig.valid_pathnames`

配置有效页面路径&标题映射参数，定义*通配页面规则*时建议配合`RouterConfig.wildcard_patterns`参数使用。

#### 4.3.4 独立渲染页面路径

> `RouterConfig.independent_core_pathnames`

设置核心页面中需要进行独立渲染的路径列表。

#### 4.3.5 公开页面路径列表

设置无需登录状态校验的公开页面路径列表，默认值：

```python
[
    "/login",
    "/logout",
    "/403-demo",
    "/404-demo",
    "/500-demo",
]
```

#### 4.3.6 侧边子菜单随访问自动展开

> `RouterConfig.side_menu_open_keys`

针对侧边菜单结构中隶属于子菜单的菜单项，配置对应需展开的上层菜单逐级`key`值列表。

#### 4.3.7 通配页面模式字典

> `RouterConfig.wildcard_patterns`

基于正则表达式，配置应用中涉及到的通配页面模式字典。

### 4.4 用户鉴权配置

#### 4.4.1 角色权限类别

> `AuthConfig.roles`

定义系统中涉及的角色权限类别。

#### 4.4.2 常规用户角色

> `AuthConfig.normal_role`

定义常规用户角色对应`AuthConfig.roles`中的键名。

#### 4.4.3 管理员角色

> `AuthConfig.admin_role`

定义管理员角色对应`AuthConfig.roles`中的键名。

#### 4.4.4 不同角色页面可访问性规则

> `AuthConfig.pathname_access_rules`

为不同角色定义对应系统中不同页面的可访问性规则。

### 4.5 数据库配置

#### 4.5.1 数据库类型

> `DatabaseConfig.database_type`

应用基础数据库类型，可选项有`'sqlite'`、`'postgresql'`、`'mysql'`，默认值：`'sqlite'`。

#### 4.5.2 PostgreSQL数据库配置

> `DatabaseConfig.postgresql_config`

当数据库类型为`'postgresql'`时，配置**PostgreSQL**数据库连接参数。

#### 4.5.3 MySQL数据库配置

> `DatabaseConfig.mysql_config`

当数据库类型为`'mysql'`时，配置**MySQL**数据库连接参数。


## 5 插件

### 快速添加页面

```cmd
python utils/add_page.py --name PagaName
```

 | 参数名 | 类型 | 默认值 | 描述 |
 |--------|------|--------|------|
 | --name | str | 无 | 页面名称（必填）/key |
 | --title | str | --name | 页面标题 |
 | --describe | str | --name | 页面描述/注释 |
 | --url | str | --name | 页面URL路径，默认/core/{--name} |
 | --icon | str | "antd-menu" | 页面图标 |