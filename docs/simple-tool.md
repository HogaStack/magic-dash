# `simple-tool` 模板介绍

`simple-tool` 是 `magic-dash` 内置的单页面工具应用模板，适合快速创建结构极简、逻辑集中、便于直接改造的 [`Dash`](https://github.com/plotly/dash) 小工具。

## 适用场景

优先选择 `simple-tool` 的典型情况：

- 只需要一个页面完成输入、计算和结果展示。
- 需要快速搭建内部数据处理工具。
- 需要将一个脚本包装成可交互网页工具。
- 页面数量、权限体系、菜单导航都不是当前重点。

如果工具后续变成多页面应用，可以迁移到 [`magic-dash`](./magic-dash.md) 模板的目录组织方式。

## 创建方式

```bash
magic-dash create --name simple-tool
```

也可以指定生成目录：

```bash
magic-dash create --name simple-tool --path ./workspace
```

命令会继续询问 `项目名称`，默认值为 `simple-tool`。最终生成路径为 `--path` 指定目录加项目名称。

## 启动方式

```bash
cd simple-tool
pip install -r requirements.txt
python app.py
```

默认访问地址：

```text
http://127.0.0.1:8050
```

## 目录结构

```text
simple-tool/
├─ app.py
└─ requirements.txt
```

`app.py` 同时承担应用初始化、页面布局、回调函数和示例业务逻辑。这个模板刻意不拆分目录，目的是让小工具开发保持低门槛。

## 内置能力

模板中的 `app.py` 默认包含：

- `Python` 版本检查：通过 [`feffery-dash-utils`](https://github.com/CNFeffery/feffery-dash-utils) 的 `check_python_version()` 检查运行时版本。
- 依赖版本检查：通过 `check_dependencies_version()` 检查 `requirements.txt` 中的关键依赖。
- `Dash` 应用实例：启用 `suppress_callback_exceptions=True`、`compress=True` 和自定义浏览器标题。
- 顶部进度条：使用 [`feffery-utils-components`](https://github.com/CNFeffery/feffery-utils-components) 的 `FefferyTopProgress`。
- 表单输入区：使用 [`feffery-antd-components`](https://github.com/CNFeffery/feffery-antd-components) 的输入框、按钮、表单项和栅格。
- 结果展示区：内置成功、失败、加载中三类交互状态示例。
- 全局消息提示：通过 `dash.set_props()` 更新全局消息容器。

## 依赖说明

`requirements.txt` 中的核心依赖包括：

```text
dash
feffery_antd_components
feffery_dash_utils
feffery_utils_components
flask-compress
```

新增业务依赖时，应同步写入 `requirements.txt`，方便部署和团队复现环境。

## 二次开发建议

常见改造顺序：

1. 修改 `app.layout` 中的标题、说明、输入项和结果区域。
2. 调整 `@app.callback` 的 `Input`、`State` 和 `Output`。
3. 将示例中的 `time.sleep()` 替换为真实业务逻辑。
4. 将结果展示替换为表格、图表、下载链接或业务组件。
5. 当文件开始膨胀时，再拆分出 `components/`、`callbacks/`、`utils/` 等目录。

更系统的扩展方式见 [二次开发介绍](./development.md)。
