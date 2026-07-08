from contextlib import contextmanager

from feffery_dash_utils.version_utils import check_dependencies_version
from sqlalchemy import create_engine, inspect, text, func, select, update
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from configs.database_config import DatabaseConfig


def get_database_url():
    """根据数据库类型配置生成SQLAlchemy连接URL"""

    if DatabaseConfig.database_type == "postgresql":
        check_dependencies_version(rules=[{"name": "psycopg2-binary"}])
        config = DatabaseConfig.postgresql_config
        return (
            "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format(
                **config
            )
        )

    if DatabaseConfig.database_type == "mysql":
        check_dependencies_version(rules=[{"name": "pymysql"}])
        config = DatabaseConfig.mysql_config
        return "mysql+pymysql://{user}:{password}@{host}:{port}/{database}".format(
            **config
        )

    return "sqlite:///magic_dash_pro.db"


# 创建SQLAlchemy引擎
# SQLite模板默认用于本地开发，需要关闭同线程限制以适应Dash/Flask请求场景
engine = create_engine(
    get_database_url(),
    future=True,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False}
    if DatabaseConfig.database_type == "sqlite"
    else {},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


class DatabaseFacade:
    """兼容少量历史db调用的轻量门面"""

    def create_tables(self, table_models):
        create_tables(table_models)

    def is_closed(self):
        return False

    def close(self):
        engine.dispose()

    def execute_sql(self, sql, params=None):
        with engine.begin() as connection:
            return connection.execute(text(sql), params or {})


db = DatabaseFacade()


class BaseModel(DeclarativeBase):
    """SQLAlchemy模型基类，补齐与Peewee模型一致的table_exists入口"""

    @classmethod
    def table_exists(cls):
        return inspect(engine).has_table(cls.__tablename__)


@contextmanager
def session_scope():
    """统一管理SQLAlchemy会话提交、回滚与关闭"""

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables(table_models):
    """创建指定内置模型对应的数据表"""

    for table_model in table_models:
        table_model.__table__.create(bind=engine, checkfirst=True)


def get_model_table_name(table_model):
    """获取模型类对应的物理表名"""

    return table_model.__tablename__


def model_table_exists(table_model):
    """检查模型类对应的数据表是否存在"""

    return table_model.table_exists()


def model_table_has_data(table_model):
    """检查模型类对应的数据表是否已有数据"""

    if not table_model.table_exists():
        return False
    with session_scope() as session:
        return (session.scalar(select(func.count()).select_from(table_model)) or 0) > 0


def ensure_user_email_schema(Users):
    """兼容旧项目中的用户邮箱字段与唯一索引"""

    table_name = Users.__tablename__
    inspector = inspect(engine)
    changes = []

    with engine.begin() as connection:
        column_names = {column["name"] for column in inspector.get_columns(table_name)}

        # 旧版本用户表可能没有user_email字段，需要就地补齐
        if "user_email" not in column_names:
            connection.execute(
                text(f"ALTER TABLE {table_name} ADD COLUMN user_email VARCHAR(255)")
            )
            changes.append("用户邮箱字段")

        # 旧版本可能用空字符串表示未设置邮箱，统一转为NULL以允许多个空邮箱
        connection.execute(
            update(Users).where(Users.user_email == "").values(user_email=None)
        )

    inspector = inspect(engine)
    indexes = inspector.get_indexes(table_name)
    unique_constraints = inspector.get_unique_constraints(table_name)
    has_unique_email_index = any(
        index.get("unique") and index.get("column_names") == ["user_email"]
        for index in indexes
    ) or any(
        constraint.get("column_names") == ["user_email"]
        for constraint in unique_constraints
    )

    if not has_unique_email_index:
        # 建立唯一索引前先检查已有邮箱是否重复，避免迁移时静默失败
        with session_scope() as session:
            duplicate_emails = [
                email
                for email, count in session.execute(
                    select(Users.user_email, func.count(Users.user_id))
                    .where(Users.user_email.is_not(None))
                    .group_by(Users.user_email)
                    .having(func.count(Users.user_id) > 1)
                )
                if count > 1
            ]

        if duplicate_emails:
            raise RuntimeError(
                "无法为用户邮箱建立唯一约束，以下邮箱存在重复：{}".format(
                    ", ".join(duplicate_emails)
                )
            )

        index_name = f"{table_name}_user_email_unique"
        with engine.begin() as connection:
            connection.execute(
                text(f"CREATE UNIQUE INDEX {index_name} ON {table_name} (user_email)")
            )
        changes.append("用户邮箱唯一约束")

    return changes


def object_to_dict(obj, columns):
    """按指定字段将模型对象转换为普通字典"""

    return {column: getattr(obj, column) for column in columns}
