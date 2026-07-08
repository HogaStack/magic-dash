from peewee import SqliteDatabase, Model, fn
from feffery_dash_utils.version_utils import check_dependencies_version
from playhouse.pool import PooledPostgresqlDatabase, PooledMySQLDatabase

from configs.database_config import DatabaseConfig


def get_db():
    """根据配置参数，创建数据库连接对象"""

    if DatabaseConfig.database_type == "postgresql":
        # 必要依赖检查
        check_dependencies_version(
            rules=[
                {
                    "name": "psycopg2-binary",
                }
            ]
        )

        # 返回postgresql类型连接池对象
        return PooledPostgresqlDatabase(
            host=DatabaseConfig.postgresql_config["host"],
            port=DatabaseConfig.postgresql_config["port"],
            user=DatabaseConfig.postgresql_config["user"],
            password=DatabaseConfig.postgresql_config["password"],
            database=DatabaseConfig.postgresql_config["database"],
            max_connections=32,
            stale_timeout=300,
        )

    elif DatabaseConfig.database_type == "mysql":
        # 必要依赖检查
        check_dependencies_version(
            rules=[
                {
                    "name": "pymysql",
                }
            ]
        )

        # 返回mysql类型连接池对象
        return PooledMySQLDatabase(
            host=DatabaseConfig.mysql_config["host"],
            port=DatabaseConfig.mysql_config["port"],
            user=DatabaseConfig.mysql_config["user"],
            passwd=DatabaseConfig.mysql_config["password"],
            database=DatabaseConfig.mysql_config["database"],
            max_connections=32,
            stale_timeout=300,
        )

    # 默认返回sqlite类型连接对象
    return SqliteDatabase("magic_dash_pro.db")


# 创建数据库连接对象
db = get_db()


class BaseModel(Model):
    """数据库表模型基类"""

    class Meta:
        # 关联数据库
        database = db


def create_tables(table_models):
    """创建指定内置模型对应的数据表"""

    db.create_tables(table_models)


def get_model_table_name(table_model):
    """获取模型类对应的物理表名"""

    return table_model._meta.table_name


def model_table_exists(table_model):
    """检查模型类对应的数据表是否存在"""

    return table_model.table_exists()


def model_table_has_data(table_model):
    """检查模型类对应的数据表是否已有数据"""

    with db.connection_context():
        return table_model.select().count() > 0


def ensure_user_email_schema(Users):
    """兼容旧项目中的用户邮箱字段与唯一索引"""

    with db.connection_context():
        table_name = Users._meta.table_name
        column_names = {column.name for column in db.get_columns(table_name)}
        changes = []

        if "user_email" not in column_names:
            db.execute_sql(
                f"ALTER TABLE {table_name} ADD COLUMN user_email VARCHAR(255)"
            )
            changes.append("用户邮箱字段")

        Users.update(user_email=None).where(Users.user_email == "").execute()

        indexes = db.get_indexes(table_name)
        has_unique_email_index = any(
            index.unique and list(index.columns) == ["user_email"] for index in indexes
        )

        if not has_unique_email_index:
            duplicate_emails = [
                item["user_email"]
                for item in (
                    Users.select(Users.user_email)
                    .where(Users.user_email.is_null(False))
                    .group_by(Users.user_email)
                    .having(fn.COUNT(Users.user_id) > 1)
                    .dicts()
                )
            ]
            if duplicate_emails:
                raise RuntimeError(
                    "无法为用户邮箱建立唯一约束，以下邮箱存在重复：{}".format(
                        ", ".join(duplicate_emails)
                    )
                )

            index_name = f"{table_name}_user_email_unique"
            db.execute_sql(
                f"CREATE UNIQUE INDEX {index_name} ON {table_name} (user_email)"
            )
            changes.append("用户邮箱唯一约束")

        return changes
