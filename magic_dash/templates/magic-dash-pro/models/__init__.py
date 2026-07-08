from importlib import import_module

from ._registry import get_engine_package


_engine_module = import_module(get_engine_package(), package=__name__)

# 将当前ORM实现的数据库能力统一暴露给初始化脚本使用
# 应用侧模块仍只需要导入具体模型类及其classmethod
db = getattr(_engine_module, "db", None)
BaseModel = getattr(_engine_module, "BaseModel", object)
create_tables = _engine_module.create_tables
get_model_table_name = _engine_module.get_model_table_name
model_table_exists = _engine_module.model_table_exists
model_table_has_data = _engine_module.model_table_has_data
ensure_user_email_schema = _engine_module.ensure_user_email_schema

__all__ = [
    "db",
    "BaseModel",
    "create_tables",
    "get_model_table_name",
    "model_table_exists",
    "model_table_has_data",
    "ensure_user_email_schema",
]
