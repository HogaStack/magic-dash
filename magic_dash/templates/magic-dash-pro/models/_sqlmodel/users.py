from typing import Any, Dict, List, Optional, Union

from sqlalchemy import Column, JSON, String, delete, select, update
from sqlmodel import Field
from werkzeug.security import check_password_hash

from configs import AuthConfig
from . import BaseModel, object_to_dict, session_scope
from .departments import Departments
from .user_permission_groups import UserPermissionGroups
from ..exceptions import ExistingUserError, InvalidUserError
from ..schema_contract import TABLE_NAMES


class Users(BaseModel, table=True):
    """SQLModel版用户信息表模型"""

    __tablename__ = TABLE_NAMES["Users"]

    user_id: str = Field(sa_column=Column(String(255), primary_key=True))
    user_name: str = Field(
        sa_column=Column(String(255), unique=True, nullable=False),
    )
    password_hash: str = Field(sa_column=Column(String(255), nullable=False))
    user_email: Optional[str] = Field(
        default=None,
        sa_column=Column(String(255), nullable=True, unique=True),
    )
    user_role: str = Field(
        default=AuthConfig.normal_role,
        sa_column=Column(String(255), nullable=False),
    )
    department_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String(255), nullable=True),
    )
    session_token: Optional[str] = Field(
        default=None,
        sa_column=Column(String(255), nullable=True),
    )
    other_info: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )

    @classmethod
    def get_user(cls, user_id: str):
        with session_scope() as session:
            return session.get(cls, user_id)

    @classmethod
    def get_user_by_name(cls, user_name: str):
        with session_scope() as session:
            return session.scalar(select(cls).where(cls.user_name == user_name))

    @classmethod
    def get_user_by_email(cls, user_email: str):
        user_email = (user_email or "").strip()
        if not user_email:
            return None
        with session_scope() as session:
            return session.scalar(select(cls).where(cls.user_email == user_email))

    @classmethod
    def get_users_by_department_id(cls, department_id: str):
        with session_scope() as session:
            records = session.scalars(
                select(cls).where(cls.department_id == department_id)
            ).all()
            return [object_to_dict(record, cls.columns()) for record in records]

    @classmethod
    def get_all_users(cls, with_department_name: bool = False):
        """获取全部用户信息，必要时联表补充部门名称"""

        with session_scope() as session:
            if with_department_name:
                rows = session.execute(
                    select(cls, Departments.department_name).join(
                        Departments,
                        cls.department_id == Departments.department_id,
                        isouter=True,
                    )
                ).all()
                return [
                    {
                        **object_to_dict(user, cls.columns()),
                        "department_name": department_name,
                    }
                    for user, department_name in rows
                ]

            records = session.scalars(select(cls)).all()
            return [object_to_dict(record, cls.columns()) for record in records]

    @classmethod
    def check_user_password(cls, user_id: str, password: str):
        return check_password_hash(cls.get_user(user_id).password_hash, password)

    @classmethod
    def add_user(
        cls,
        user_id: str,
        user_name: str,
        password_hash: str,
        user_email: str = None,
        department_id: str = None,
        user_role: str = "normal",
        other_info: Union[Dict, List] = None,
    ):
        """添加用户，并保持与Peewee实现一致的校验规则"""

        with session_scope() as session:
            user_email = (user_email or "").strip() or None
            if not (user_id and user_name and password_hash):
                raise InvalidUserError("用户信息不完整")
            if session.get(cls, user_id):
                raise ExistingUserError("用户id已存在")
            if session.scalar(select(cls).where(cls.user_name == user_name)):
                raise ExistingUserError("用户名已存在")
            if user_email and session.scalar(
                select(cls).where(cls.user_email == user_email)
            ):
                raise ExistingUserError("邮箱已被其他用户使用")
            if not UserPermissionGroups.is_role_valid(user_role):
                raise InvalidUserError("用户角色不正确")

            session.add(
                cls(
                    user_id=user_id,
                    user_name=user_name,
                    password_hash=password_hash,
                    user_email=user_email,
                    department_id=department_id,
                    user_role=user_role,
                    other_info=other_info,
                )
            )

    @classmethod
    def delete_user(cls, user_id: str):
        """删除用户，同时清理对应OTP凭据"""

        with session_scope() as session:
            from .otp_credentials import OtpCredentials

            if OtpCredentials.table_exists():
                session.execute(
                    delete(OtpCredentials).where(OtpCredentials.user_id == user_id)
                )
            session.execute(delete(cls).where(cls.user_id == user_id))

    @classmethod
    def truncate_users(cls, execute: bool = False):
        if execute:
            with session_scope() as session:
                from .otp_credentials import OtpCredentials

                if OtpCredentials.table_exists():
                    session.execute(delete(OtpCredentials))
                session.execute(delete(cls))

    @classmethod
    def update_user(cls, user_id: str, **kwargs):
        """更新用户信息，并返回更新后的用户对象"""

        with session_scope() as session:
            if "user_email" in kwargs:
                user_email = (kwargs["user_email"] or "").strip() or None
                kwargs["user_email"] = user_email
                duplicate_user = (
                    session.scalar(
                        select(cls).where(
                            (cls.user_email == user_email) & (cls.user_id != user_id)
                        )
                    )
                    if user_email
                    else None
                )
                if duplicate_user:
                    raise ExistingUserError("邮箱已被其他用户使用")

            if "user_role" in kwargs and not UserPermissionGroups.is_role_valid(
                kwargs["user_role"]
            ):
                raise InvalidUserError("用户角色不正确")

            session.execute(update(cls).where(cls.user_id == user_id).values(**kwargs))
            session.flush()
            return session.get(cls, user_id)

    @classmethod
    def alter_department_members(
        cls,
        department_id: str,
        origin_user_ids: list = None,
        target_user_ids: list = None,
    ):
        origin_user_ids = origin_user_ids or []
        target_user_ids = target_user_ids or []
        with session_scope() as session:
            removed_user_ids = [
                user_id for user_id in origin_user_ids if user_id not in target_user_ids
            ]
            if removed_user_ids:
                session.execute(
                    update(cls)
                    .where(cls.user_id.in_(removed_user_ids))
                    .values(department_id=None)
                )
            if target_user_ids:
                session.execute(
                    update(cls)
                    .where(cls.user_id.in_(target_user_ids))
                    .values(department_id=department_id)
                )

    @classmethod
    def columns(cls):
        return [
            "user_id",
            "user_name",
            "password_hash",
            "user_email",
            "user_role",
            "department_id",
            "session_token",
            "other_info",
        ]
