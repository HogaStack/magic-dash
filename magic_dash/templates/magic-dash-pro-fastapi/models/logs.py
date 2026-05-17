from typing import List, Literal
from peewee import AutoField, CharField, DateTimeField

from . import db, BaseModel


class LoginLogs(BaseModel):
    """登录日志表模型类"""

    # 记录id，主键，自增
    id = AutoField()

    # 登录用户名称
    user_name = CharField()

    # 登录用户id
    user_id = CharField(null=True)

    # IP地址
    ip = CharField()

    # 浏览器
    browser = CharField(null=True)

    # 操作系统
    os = CharField(null=True)

    # 登录状态
    status = CharField()

    # 登录时间
    login_datetime = DateTimeField()

    @classmethod
    def get_count(cls) -> int:
        """获取日志记录总数"""

        with db.connection_context():
            return cls.select().count()

    @classmethod
    def get_logs(
        cls,
        limit: int = None,
        offset: int = None,
        order_by: Literal["id", "user_name", "status", "login_datetime"] = "id",
        order: Literal["ascend", "descend"] = "descend",
        user_name_keyword: str = None,
    ):
        """条件性获取日志记录"""

        with db.connection_context():
            # 构造查询
            query = cls.select()
            # 若用户名关键词检索条件有效
            if user_name_keyword:
                query = query.where(cls.user_name.contains(user_name_keyword))
            # 若排序条件有效
            if order_by and order:
                if order == "ascend":
                    query = query.order_by(getattr(cls, order_by))
                else:
                    query = query.order_by(getattr(cls, order_by).desc())
            # 若分页相关参数有效
            if limit and offset:
                query = query.limit(limit).offset(offset)
            # 返回查询结果
            return list(query.dicts())

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
        """添加日志记录"""

        with db.connection_context():
            # 执行日志记录添加操作
            with db.atomic():
                cls.create(
                    user_name=user_name,
                    user_id=user_id,
                    ip=ip,
                    browser=browser,
                    os=os,
                    status=status,
                    login_datetime=login_datetime,
                )

    @classmethod
    def delete_logs(cls, log_ids: List[str]):
        """删除指定日志记录"""

        with db.connection_context():
            with db.atomic():
                cls.delete().where(cls.id << log_ids).execute()

    @classmethod
    def truncate_logs(cls):
        """清空日志记录"""

        with db.connection_context():
            with db.atomic():
                cls.delete().execute()


# 创建表（如果表不存在）
db.create_tables([LoginLogs])
