# `magic-dash` 命令使用

`magic-dash` 命令是本项目暴露给用户的主要入口。它基于 [`click`](https://github.com/pallets/click)、[`questionary`](https://github.com/tmbo/questionary) 和 [`rich`](https://github.com/Textualize/rich) 实现，用于查看模板列表和生成项目。

## 安装

```bash
pip install magic-dash -U
```

本地开发仓库时可使用：

```bash
pip install -e .
```

## 查看版本

```bash
magic-dash --version
```

版本号来自 `magic_dash/__init__.py` 中的 `__version__`。

## 查看帮助

```bash
magic-dash --help
magic-dash list --help
magic-dash create --help
```

## 查看模板列表

```bash
magic-dash list
```

当前可直接选择的顶层模板：

```text
magic-dash
magic-dash-pro
simple-tool
```

`magic-dash-pro-fastapi` 是内部隐藏模板，不会出现在列表中。

## 交互式创建项目

不传入 `--name` 时，会进入模板选择菜单：

```bash
magic-dash create
```

选择模板后，命令会继续询问 `项目名称`。如果目标目录下已经存在同名文件夹，会提示重新输入项目名称。

## 指定模板创建项目

```bash
magic-dash create --name simple-tool
magic-dash create --name magic-dash
magic-dash create --name magic-dash-pro
```

`--name` 只能使用顶层模板名。以下命令是无效的：

```bash
magic-dash create --name magic-dash-pro-fastapi
```

## 指定生成目录

```bash
magic-dash create --name magic-dash --path ./workspace
```

`--path` 表示项目生成的父目录。命令仍会询问项目名称，最终生成路径为：

```text
./workspace/项目名称
```

## `magic-dash-pro` 后端选择

创建 `magic-dash-pro` 时，会出现后端类型选择：

- `Flask`：默认后端。
- `FastAPI`：可选后端。

交互式方式：

```bash
magic-dash create --name magic-dash-pro
```

后端类型仅通过交互式菜单选择。

## 生成后的提示

项目生成成功后，命令会输出后续启动步骤：

```bash
cd 项目名称
pip install -r requirements.txt
python app.py
```

如果模板为 `magic-dash-pro`，会额外提示：

```bash
python -m models.init_db
```

## 错误处理

### 模板名不存在

```bash
magic-dash create --name unknown-template
```

命令会报错并列出可用模板名。

### 项目文件夹已存在

如果目标目录下已经存在同名文件夹，命令不会覆盖旧目录，而是要求重新输入项目名称。

### 取消交互

在模板选择或后端选择过程中取消操作，命令会停止生成，不会写入项目文件。

## 实现说明

`create` 命令的核心行为是复制 `magic_dash/templates/` 下的模板目录到目标路径。对于 `magic-dash`、`magic-dash-pro` 和 `magic-dash-pro-fastapi`，生成后还会把 `configs/base_config.py` 中的 `app_version` 替换为当前 `magic-dash` 版本号。
