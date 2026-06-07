# `CLI`命令说明

`magic-dash`命令是项目脚手架的主要入口，用于查看内置模板、创建模板项目和确认当前安装版本。

## 安装与更新

```bash
pip install magic-dash -U
```

## 全局命令

### 查看版本

```bash
magic-dash --version
```

### 查看帮助

```bash
magic-dash --help
```

查看子命令帮助：

```bash
magic-dash list --help
magic-dash create --help
```

## `magic-dash list`

列出当前可直接创建的全部内置模板：

```bash
magic-dash list
```

当前顶层模板为：

| 模板 | 说明 |
| --- | --- |
| `magic-dash` | 适用于多页面、持续扩展的应用模板 |
| `magic-dash-pro` | 适用于多页面、持续扩展的管理型应用模板，支持复杂用户与部门关系、用户登录、管理和鉴权能力 |
| `simple-tool` | 单页面工具应用模板 |

`magic-dash-pro-fastapi`是`magic-dash-pro`的内部`FastAPI`后端变体，不会出现在顶层模板列表中，也不能通过`--name magic-dash-pro-fastapi`直接创建。

## `magic-dash create`

创建指定模板项目：

```bash
magic-dash create [OPTIONS]
```

可用选项：

| 选项 | 默认值 | 说明 |
| --- | --- | --- |
| `--name` | 无 | [Dash](https://github.com/plotly/dash)应用项目模板名称；可选`simple-tool`、`magic-dash`、`magic-dash-pro` |
| `--path` | `"."` | 项目生成目标父目录 |

## 交互式创建

不传入`--name`时，命令会进入模板选择菜单：

```bash
magic-dash create
```

选择模板后，命令会继续提示输入项目名称。如果目标父目录下已存在同名文件夹，会要求重新输入项目名称，避免覆盖已有项目。

## 指定模板创建

```bash
magic-dash create --name simple-tool
magic-dash create --name magic-dash
magic-dash create --name magic-dash-pro
```

指定生成父目录：

```bash
magic-dash create --name magic-dash --path ./workspace
```

如果项目名称为`demo-app`，最终生成路径为：

```text
./workspace/demo-app
```

## `magic-dash-pro`后端选择

创建`magic-dash-pro`时，命令会提示选择后端类型：

| 选项 | 说明 |
| --- | --- |
| `Flask` | 默认后端，基于`flask-login` |
| `FastAPI` | 可选后端，基于`fastapi-login` |

示例：

```bash
magic-dash create --name magic-dash-pro
```

后端类型当前通过交互式菜单选择。

## 生成后的启动提示

项目生成成功后，命令会提示进入目录、安装依赖并启动应用：

```bash
cd 项目名称
pip install -r requirements.txt
python app.py
```

如果创建的是`magic-dash-pro`，还需要先初始化数据库和默认管理员账号：

```bash
python -m magic_init
python app.py
```

默认管理员账号：

```text
用户名：admin
初始密码：admin123
```

## 错误处理

### 模板名称不存在

```bash
magic-dash create --name unknown-template
```

命令会报错，并列出可用模板名称。

### 直接创建`FastAPI`内部变体

```bash
magic-dash create --name magic-dash-pro-fastapi
```

该命令无效。请使用`magic-dash create --name magic-dash-pro`，再在后端类型菜单中选择`FastAPI`。

### 项目文件夹已存在

如果目标父目录下已经存在同名文件夹，命令不会覆盖旧目录，而是提示重新输入项目名称。

### 取消交互

在模板选择或`magic-dash-pro`后端选择过程中取消操作，命令会停止生成，不写入项目文件。
