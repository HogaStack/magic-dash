from importlib import import_module


# 不同ORM引擎对应的模型实现包
# 后续接入新的ORM时，只需要新增实现包并在这里登记
ENGINE_PACKAGES = {
    "peewee": "._peewee",
    "sqlalchemy": "._sqlalchemy",
    "sqlmodel": "._sqlmodel",
}


def get_engine_package():
    """获取源码模板的默认ORM实现包。

    真实项目会在magic-dash create阶段物化为单一ORM实现；
    这里仅用于源码模板被直接导入时保持历史默认行为。
    """

    return ENGINE_PACKAGES["peewee"]


def import_engine_module(module_name: str):
    """导入当前ORM实现包中的同名模型模块"""

    return import_module(f"{get_engine_package()}.{module_name}", package=__package__)


def load_model(module_name: str, class_name: str):
    """加载当前ORM实现下的模型类，供外层models/*.py稳定导出"""

    return getattr(import_engine_module(module_name), class_name)
