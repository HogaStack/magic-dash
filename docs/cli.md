# `CLI`命令说明

`magic-dash`命令是项目脚手架的主要入口，用于查看内置模板、创建模板项目、管理内置模板公共静态资源和确认当前安装版本。

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
magic-dash init-assets --help
magic-dash remove-assets --help
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
| `magic-dash-pro` | 适用于多页面、持续扩展的管理型应用模板，支持复杂用户与部门关系、用户名密码、邮件验证码及`OTP`动态口令登录、管理和鉴权能力 |
| `simple-tool` | 单页面工具应用模板 |

`magic-dash-pro-fastapi`是`magic-dash-pro`的内部`FastAPI`后端变体，不会出现在顶层模板列表中，也不能通过`--name magic-dash-pro-fastapi`直接创建。

## `magic-dash create`

创建指定模板项目：

```bash
magic-dash create [OPTIONS]
```

可用选项：

| 选项 | 简写 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `--name` | `-n` | 无 | [Dash](https://github.com/plotly/dash)应用项目模板名称；可选`simple-tool`、`magic-dash`、`magic-dash-pro` |
| `--path` | `-p` | `"."` | 项目生成目标父目录 |
| `--backend` | `-b` | 交互选择 | 后端类型；可选`flask`、`fastapi` |

长参数和简写参数完全等价，例如`--name`可写作`-n`，`--path`可写作`-p`，`--backend`可写作`-b`。

## 交互式创建

不传入`--name`时，命令会进入模板选择菜单：

```bash
magic-dash create
```

选择模板后，命令会继续提示选择后端类型并输入项目名称。如果目标父目录下已存在同名文件夹，会要求重新输入项目名称，避免覆盖已有项目。

## 指定模板创建

```bash
magic-dash create --name simple-tool
magic-dash create --name magic-dash
magic-dash create --name magic-dash-pro
```

指定生成父目录和后端类型：

```bash
magic-dash create --name simple-tool --backend flask --path ./workspace
magic-dash create --name magic-dash --backend fastapi --path ./workspace
magic-dash create --name magic-dash-pro --backend fastapi --path ./workspace
```

也可以使用简写参数：

```bash
magic-dash create -n simple-tool -b flask -p ./workspace
magic-dash create -n magic-dash -b fastapi -p ./workspace
magic-dash create -n magic-dash-pro -b fastapi -p ./workspace
```

如果项目名称为`demo-app`，最终生成路径为：

```text
./workspace/demo-app
```

## 后端选择

创建`simple-tool`、`magic-dash`或`magic-dash-pro`时，命令会提示选择后端类型：

| 选项 | 说明 |
| --- | --- |
| `Flask` | 默认后端 |
| `FastAPI` | 可选后端 |

示例：

```bash
magic-dash create --name simple-tool --backend fastapi
magic-dash create --name magic-dash --backend fastapi
magic-dash create --name magic-dash-pro --backend fastapi
```

等价的简写形式：

```bash
magic-dash create -n simple-tool -b fastapi
magic-dash create -n magic-dash -b fastapi
magic-dash create -n magic-dash-pro -b fastapi
```

`simple-tool`和`magic-dash`选择`FastAPI`后端时，会在复制原始模板后轻量改写生成结果：`requirements.txt`会切换到`dash[fastapi]`并补充`fastapi`、`uvicorn`依赖，`dash.Dash()`实例会添加`backend="fastapi"`。`magic-dash`中的浏览器版本检查也会从`Flask before_request`改写为`FastAPI middleware`。

`magic-dash-pro`选择`FastAPI`后端时，仍使用内部维护的`magic-dash-pro-fastapi`模板变体，以适配登录、鉴权和权限管理等复杂差异。

## `magic-dash create`与公共静态资源

`magic-dash-pro`及其内部`FastAPI`变体的登录页会使用下列公共静态资源：

```text
assets/videos/login-bg.mp4
assets/imgs/login/gradient-bg.jpg
assets/imgs/login/gradient-bg-side.png
```

为了减少源码仓库和发布包中的重复大文件，内置模板目录默认不保存这些资源副本，而是统一保存在`magic_dash/public_assets/`中。

使用`magic-dash create --name magic-dash-pro`创建项目时，命令会在复制模板后自动把这些公共静态资源复制到生成项目的`assets/`目录，并在终端输出复制状态。开发者通常不需要手动处理。

## `magic-dash init-assets`

将`magic_dash/public_assets/`中的公共静态资源同步到内置`magic-dash-pro`和`magic-dash-pro-fastapi`模板目录。该命令主要用于源码仓库开发场景，例如需要直接运行或检查内置模板目录时：

```bash
magic-dash init-assets
```

如果目标模板目录下已经存在相关资源文件，命令会批量确认一次是否覆盖，不会逐个文件重复询问。

强制覆盖已有资源文件：

```bash
magic-dash init-assets --force
```

等价的简写形式：

```bash
magic-dash init-assets -f
```

## `magic-dash remove-assets`

移除内置`magic-dash-pro`和`magic-dash-pro-fastapi`模板目录下的公共静态资源副本：

```bash
magic-dash remove-assets
```

该命令只会处理公共资源映射中的模板副本，不会删除`magic_dash/public_assets/`中的原始公共资源。它适合在本地执行过`init-assets`后，发布或提交前清理模板目录下的大文件副本。

如果检测到可移除文件，命令会批量确认一次是否移除。强制移除：

```bash
magic-dash remove-assets --force
```

等价的简写形式：

```bash
magic-dash remove-assets -f
```

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

初始化过程会提示填写可选的管理员邮箱，并通过表格展示用户、部门、邮件验证码和`OTP`凭据等内置数据表的创建记录。邮件验证码登录和`OTP`动态口令登录默认关闭，启用方式及相关配置见[`magic-dash-pro`配置参数](./magic-dash-pro/配置参数.md)。

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

该命令无效。请使用`magic-dash create --name magic-dash-pro --backend fastapi`，或使用`magic-dash create --name magic-dash-pro`后在后端类型菜单中选择`FastAPI`。

### 项目文件夹已存在

如果目标父目录下已经存在同名文件夹，命令不会覆盖旧目录，而是提示重新输入项目名称。

### 取消交互

在模板选择或后端选择过程中取消操作，命令会停止生成，不写入项目文件。
