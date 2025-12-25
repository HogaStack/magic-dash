from peewee import CharField, JOIN
from typing import Union, Dict, List
from playhouse.sqlite_ext import JSONField
from werkzeug.security import check_password_hash

from . import db, BaseModel
from configs import AuthConfig
from .departments import Departments
from .exceptions import InvalidUserError, ExistingUserError


class Users(BaseModel):
    """用户信息表模型类"""

    # 用户id，主键
    user_id = CharField(primary_key=True)

    # 用户名，唯一
    user_name = CharField(unique=True)

    # 用户密码散列值
    password_hash = CharField()

    # 用户角色，全部可选项见configs.AuthConfig.roles
    user_role = CharField(default=AuthConfig.normal_role)

    # 用户所属部门id，允许空值
    department_id = CharField(null=True)

    # 用户最近一次登录会话token
    session_token = CharField(null=True)

    # 用户其他辅助信息，任意JSON格式，允许空值
    other_info = JSONField(null=True)

    @classmethod
    def get_user(cls, user_id: str):
        """根据用户id查询用户信息"""

        with db.connection_context():
            return cls.get_or_none(cls.user_id == user_id)

    @classmethod
    def get_user_by_name(cls, user_name: str):
        """根据用户名查询用户信息"""

        with db.connection_context():
            return cls.get_or_none(cls.user_name == user_name)

    @classmethod
    def get_users_by_department_id(cls, department_id: str):
        """根据部门id查询用户信息"""

        with db.connection_context():
            return list(cls.select().where(cls.department_id == department_id).dicts())

    @classmethod
    def get_all_users(cls, with_department_name: bool = False):
        """获取所有用户信息"""

        with db.connection_context():
            # 若需要额外携带部门名称信息
            if with_department_name:
                return list(
                    # 选择Users表全部字段、Departments表的department_name字段
                    cls.select(cls, Departments.department_name)
                    .join(
                        Departments,
                        JOIN.LEFT_OUTER,
                        on=(cls.department_id == Departments.department_id),
                    )
                    .dicts()
                )
            return list(cls.select().dicts())

    @classmethod
    def check_user_password(cls, user_id: str, password: str):
        """校验用户密码"""

        return check_password_hash(cls.get_user(user_id).password_hash, password)

    @classmethod
    def add_user(
        cls,
        user_id: str,
        user_name: str,
        password_hash: str,
        department_id: str = None,
        user_role: str = "normal",
        other_info: Union[Dict, List] = None,
    ):
        """添加用户"""

        with db.connection_context():
            # 若必要用户信息不完整
            if not (user_id and user_name and password_hash):
                raise InvalidUserError("用户信息不完整")

            # 若用户id已存在
            elif cls.get_or_none(cls.user_id == user_id):
                raise ExistingUserError("用户id已存在")

            # 若用户名存在重复
            elif cls.get_or_none(cls.user_name == user_name):
                raise ExistingUserError("用户名已存在")

            # 执行用户添加操作
            with db.atomic():
                cls.create(
                    user_id=user_id,
                    user_name=user_name,
                    password_hash=password_hash,
                    department_id=department_id,
                    user_role=user_role,
                    other_info=other_info,
                )

    @classmethod
    def delete_user(cls, user_id: str):
        """删除用户"""

        with db.connection_context():
            with db.atomic():
                cls.delete().where(cls.user_id == user_id).execute()

    @classmethod
    def truncate_users(cls, execute: bool = False):
        """清空用户，请小心使用"""

        # 若保险参数execute=True
        if execute:
            with db.connection_context():
                with db.atomic():
                    cls.delete().execute()

    @classmethod
    def update_user(cls, user_id: str, **kwargs):
        """更新用户信息"""

        with db.connection_context():
            with db.atomic():
                cls.update(**kwargs).where(cls.user_id == user_id).execute()

            # 返回成功更新后的用户信息
            return cls.get_or_none(cls.user_id == user_id)

    @classmethod
    def alter_department_members(
        cls,
        department_id: str,
        origin_user_ids: list = None,
        target_user_ids: list = None,
    ):
        """更改用户所属部门"""

        with db.connection_context():
            with db.atomic():
                # 将本次操作被移出部门的用户所属部门更新为空
                (
                    cls.update(department_id=None)
                    .where(
                        cls.user_id
                        << [
                            user_id
                            for user_id in origin_user_ids
                            if user_id not in target_user_ids
                        ]
                    )
                    .execute()
                )

                # 将本次操作被移入部门的用户所属部门更新为目标部门
                (
                    cls.update(department_id=department_id)
                    .where(cls.user_id << target_user_ids)
                    .execute()
                )
