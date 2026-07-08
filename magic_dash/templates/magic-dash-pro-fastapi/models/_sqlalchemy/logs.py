from datetime import datetime
from typing import List, Literal

from sqlalchemy import DateTime, Integer, String, delete, func, select
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel, engine, object_to_dict, session_scope
from ..schema_contract import TABLE_NAMES


class LoginLogs(BaseModel):
    """SQLAlchemy版登录日志表模型"""

    __tablename__ = TABLE_NAMES["LoginLogs"]

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[str] = mapped_column(String(255), nullable=True)
    ip: Mapped[str] = mapped_column(String(255))
    browser: Mapped[str] = mapped_column(String(255), nullable=True)
    os: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(255))
    login_datetime: Mapped[datetime] = mapped_column(DateTime)

    @classmethod
    def get_count(cls) -> int:
        with session_scope() as session:
            return session.scalar(select(func.count()).select_from(cls)) or 0

    @classmethod
    def get_logs(
        cls,
        limit: int = None,
        offset: int = None,
        order_by: Literal["id", "user_name", "status", "login_datetime"] = "id",
        order: Literal["ascend", "descend"] = "descend",
        user_name_keyword: str = None,
    ):
        """按筛选、排序和分页条件获取登录日志字典列表"""

        with session_scope() as session:
            query = select(cls)
            if user_name_keyword:
                query = query.where(cls.user_name.contains(user_name_keyword))
            if order_by and order:
                order_column = getattr(cls, order_by)
                query = query.order_by(
                    order_column.asc() if order == "ascend" else order_column.desc()
                )
            if limit and offset:
                query = query.limit(limit).offset(offset)
            records = session.scalars(query).all()
            return [cls.to_dict(record) for record in records]

    @classmethod
    def add_log(
        cls,
        user_name: str,
        user_id: str,
        ip: str,
        browser: str,
        os: str,
        status: str,
        login_datetime: str,
    ):
        with session_scope() as session:
            # 应用回调中传入的是格式化后的字符串，这里统一转换为datetime入库
            if isinstance(login_datetime, str):
                login_datetime = datetime.strptime(
                    login_datetime,
                    "%Y-%m-%d %H:%M:%S",
                )

            session.add(
                cls(
                    user_name=user_name,
                    user_id=user_id,
                    ip=ip,
                    browser=browser,
                    os=os,
                    status=status,
                    login_datetime=login_datetime,
                )
            )

    @classmethod
    def delete_logs(cls, log_ids: List[str]):
        with session_scope() as session:
            session.execute(delete(cls).where(cls.id.in_(log_ids)))

    @classmethod
    def truncate_logs(cls):
        with session_scope() as session:
            session.execute(delete(cls))

    @classmethod
    def columns(cls):
        return [
            "id",
            "user_name",
            "user_id",
            "ip",
            "browser",
            "os",
            "status",
            "login_datetime",
        ]

    @classmethod
    def to_dict(cls, record):
        result = object_to_dict(record, cls.columns())
        if isinstance(result["login_datetime"], datetime):
            result["login_datetime"] = result["login_datetime"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        return result


# 保持Peewee旧实现的导入时建表行为，避免日志页首次访问时报表不存在
LoginLogs.__table__.create(bind=engine, checkfirst=True)
