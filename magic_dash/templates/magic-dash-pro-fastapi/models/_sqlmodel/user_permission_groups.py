from typing import Any, Dict, List, Optional, Union

from sqlalchemy import Boolean, Column, JSON, String, delete, func, select, update
from sqlmodel import Field

from configs import AuthConfig, RouterConfig
from . import BaseModel, create_tables, object_to_dict, session_scope
from ..exceptions import ExistingPermissionGroupError, InvalidPermissionGroupError
from ..schema_contract import TABLE_NAMES


class UserPermissionGroups(BaseModel, table=True):
    """SQLModel版用户权限分组表模型"""

    __tablename__ = TABLE_NAMES["UserPermissionGroups"]

    permission_group_id: str = Field(
        sa_column=Column(String(255), primary_key=True),
    )
    permission_group_name: str = Field(
        sa_column=Column(String(255), unique=True, nullable=False),
    )
    access_rule_type: str = Field(
        default="exclude",
        sa_column=Column(String(255), nullable=False),
    )
    access_rule_keys: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    is_builtin: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False),
    )
    other_info: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )

    @classmethod
    def ensure_table(cls):
        """确保权限分组表存在，并清理不允许入库的admin记录"""

        if not cls.table_exists():
            create_tables([cls])
        with session_scope() as session:
            session.execute(
                delete(cls).where(cls.permission_group_id == AuthConfig.admin_role)
            )

    @classmethod
    def normalize_access_rule(
        cls,
        access_rule_type: str = "exclude",
        access_rule_keys: List[str] = None,
    ):
        if access_rule_type not in ["all", "include", "exclude"]:
            raise InvalidPermissionGroupError("权限规则类型不正确")

        if access_rule_type == "all":
            return {"type": access_rule_type, "keys": []}

        if access_rule_keys in [None, ""]:
            access_rule_keys = []
        if not isinstance(access_rule_keys, list):
            raise InvalidPermissionGroupError("权限规则keys必须为列表")
        if any(not isinstance(item, str) for item in access_rule_keys):
            raise InvalidPermissionGroupError("权限规则keys必须为字符串列表")

        invalid_access_rule_keys = [
            item
            for item in access_rule_keys
            if item not in cls.get_valid_access_rule_keys()
        ]
        if invalid_access_rule_keys:
            raise InvalidPermissionGroupError(
                "权限规则keys包含无效页面：{}".format(
                    "、".join(invalid_access_rule_keys)
                )
            )

        return {"type": access_rule_type, "keys": access_rule_keys}

    @staticmethod
    def get_valid_access_rule_keys():
        return {
            pathname
            for pathname in RouterConfig.valid_pathnames
            if isinstance(pathname, str)
            and pathname not in RouterConfig.public_pathnames
        }

    @classmethod
    def get_effective_roles(cls):
        """获取配置参数与数据库综合后的有效用户角色信息"""

        database_permission_groups = {
            item["permission_group_id"]: item
            for item in cls.get_all_permission_groups()
        }
        effective_roles = {
            role_id: {
                "description": (
                    database_permission_groups[role_id]["permission_group_name"]
                    if role_id != AuthConfig.admin_role
                    and role_id in database_permission_groups
                    and cls.get_permission_group_conflict(
                        database_permission_groups[role_id]
                    )["type"]
                    == "config_override"
                    else role_info["description"]
                ),
                "source": "config",
                "is_builtin": True,
            }
            for role_id, role_info in AuthConfig.roles.items()
        }

        for permission_group in database_permission_groups.values():
            permission_group_id = permission_group["permission_group_id"]
            if permission_group_id in effective_roles:
                continue
            if cls.get_permission_group_conflict(permission_group)["type"]:
                continue
            effective_roles[permission_group_id] = {
                "description": permission_group["permission_group_name"],
                "source": "database",
                "is_builtin": permission_group["is_builtin"],
            }

        return effective_roles

    @staticmethod
    def get_config_role_names(exclude_role_id: str = None):
        return [
            role_info["description"]
            for role_id, role_info in AuthConfig.roles.items()
            if role_id != exclude_role_id
        ]

    @classmethod
    def get_permission_group_conflict(cls, permission_group: dict):
        permission_group_id = permission_group["permission_group_id"]
        permission_group_name = permission_group["permission_group_name"]

        if permission_group_id == AuthConfig.admin_role:
            return {
                "type": "admin_database_forbidden",
                "label": "admin数据库记录禁用",
                "message": "admin权限组只允许通过硬编码配置定义，不允许存储为数据库权限组。",
            }

        if permission_group_name in cls.get_config_role_names(
            exclude_role_id=permission_group_id
        ):
            return {
                "type": "config_name_conflict",
                "label": "名称冲突",
                "message": "权限组名称与硬编码权限组名称冲突。",
            }

        if (
            "access_rule_type" in permission_group
            and "access_rule_keys" in permission_group
        ):
            try:
                cls.normalize_access_rule(
                    permission_group["access_rule_type"],
                    permission_group["access_rule_keys"],
                )
            except InvalidPermissionGroupError as e:
                return {
                    "type": "invalid_access_rule",
                    "label": "规则异常",
                    "message": "数据库权限组页面访问规则无效：{}".format(str(e)),
                }

        if permission_group_id in AuthConfig.roles:
            return {
                "type": "config_override",
                "label": "数据库覆盖",
                "message": "当前数据库记录覆盖同id硬编码权限组的名称与页面访问规则。",
            }

        return {"type": None, "label": "正常", "message": None}

    @staticmethod
    def format_access_rule_keys(access_rule_keys: List = None):
        if not access_rule_keys:
            return []
        return [
            item.pattern if hasattr(item, "pattern") else item
            for item in access_rule_keys
        ]

    @classmethod
    def get_effective_role_options(cls):
        return [
            {"label": role_info["description"], "value": role_id}
            for role_id, role_info in cls.get_effective_roles().items()
        ]

    @classmethod
    def get_role_description(cls, permission_group_id: str, default: str = "未知角色"):
        return (
            cls.get_effective_roles()
            .get(permission_group_id, {})
            .get("description", default)
        )

    @classmethod
    def is_role_valid(cls, permission_group_id: str):
        return permission_group_id in cls.get_effective_roles()

    @classmethod
    def get_permission_group_user_count(cls, permission_group_id: str):
        permission_group_id = (permission_group_id or "").strip()
        if not permission_group_id:
            return 0

        from .users import Users

        if not Users.table_exists():
            return 0
        with session_scope() as session:
            return (
                session.scalar(
                    select(func.count())
                    .select_from(Users)
                    .where(Users.user_role == permission_group_id)
                )
                or 0
            )

    @classmethod
    def get_effective_pathname_access_rule(cls, permission_group_id: str):
        match_group = cls.get_permission_group(permission_group_id)
        if permission_group_id == AuthConfig.admin_role:
            return AuthConfig.pathname_access_rules.get(permission_group_id)

        if permission_group_id in AuthConfig.roles:
            if (
                match_group
                and cls.get_permission_group_conflict(cls.to_dict(match_group))["type"]
                == "config_override"
            ):
                return cls.normalize_access_rule(
                    match_group.access_rule_type,
                    match_group.access_rule_keys,
                )
            return AuthConfig.pathname_access_rules.get(permission_group_id)

        if not match_group:
            return None
        if cls.get_permission_group_conflict(cls.to_dict(match_group))["type"]:
            return None
        return cls.normalize_access_rule(
            match_group.access_rule_type,
            match_group.access_rule_keys,
        )

    @classmethod
    def get_effective_pathname_access_rules(cls):
        effective_rules = {}
        for permission_group_id in AuthConfig.roles:
            effective_rules[permission_group_id] = (
                cls.get_effective_pathname_access_rule(permission_group_id)
            )

        for permission_group in cls.get_all_permission_groups():
            permission_group_id = permission_group["permission_group_id"]
            if permission_group_id in effective_rules:
                continue
            if cls.get_permission_group_conflict(permission_group)["type"]:
                continue
            effective_rules[permission_group_id] = cls.normalize_access_rule(
                permission_group["access_rule_type"],
                permission_group["access_rule_keys"],
            )

        return effective_rules

    @classmethod
    def get_effective_permission_group_records(cls):
        """获取权限管理页面使用的综合权限分组记录"""

        database_permission_groups = {
            item["permission_group_id"]: item
            for item in cls.get_all_permission_groups()
        }
        records = []

        for permission_group_id, role_info in AuthConfig.roles.items():
            match_group = database_permission_groups.get(permission_group_id)
            conflict = (
                cls.get_permission_group_conflict(match_group)
                if match_group
                else {"type": None, "label": "正常", "message": None}
            )
            access_rule = cls.get_effective_pathname_access_rule(
                permission_group_id
            ) or {"type": "exclude", "keys": []}

            records.append(
                {
                    "permission_group_id": permission_group_id,
                    "permission_group_name": (
                        match_group["permission_group_name"]
                        if permission_group_id != AuthConfig.admin_role
                        and match_group
                        and conflict["type"] == "config_override"
                        else role_info["description"]
                    ),
                    "access_rule_type": access_rule["type"],
                    "access_rule_keys": cls.format_access_rule_keys(
                        access_rule.get("keys", [])
                    ),
                    "source": "config",
                    "source_label": "硬编码权限组",
                    "conflict_type": conflict["type"],
                    "conflict_label": conflict["label"],
                    "conflict_message": conflict["message"],
                    "is_admin": permission_group_id == AuthConfig.admin_role,
                    "database_exists": bool(match_group),
                    "other_info": match_group["other_info"] if match_group else None,
                }
            )

        for permission_group in database_permission_groups.values():
            permission_group_id = permission_group["permission_group_id"]
            if permission_group_id in AuthConfig.roles:
                continue
            conflict = cls.get_permission_group_conflict(permission_group)
            records.append(
                {
                    "permission_group_id": permission_group_id,
                    "permission_group_name": permission_group["permission_group_name"],
                    "access_rule_type": permission_group["access_rule_type"],
                    "access_rule_keys": cls.format_access_rule_keys(
                        permission_group["access_rule_keys"]
                    ),
                    "source": "database",
                    "source_label": "数据库权限组",
                    "conflict_type": conflict["type"],
                    "conflict_label": conflict["label"],
                    "conflict_message": conflict["message"],
                    "is_admin": False,
                    "database_exists": True,
                    "other_info": permission_group["other_info"],
                }
            )

        return records

    @classmethod
    def get_permission_group(cls, permission_group_id: str):
        permission_group_id = (permission_group_id or "").strip()
        if not permission_group_id:
            return None
        cls.ensure_table()
        with session_scope() as session:
            return session.get(cls, permission_group_id)

    @classmethod
    def get_permission_group_by_name(cls, permission_group_name: str):
        permission_group_name = (permission_group_name or "").strip()
        if not permission_group_name:
            return None
        cls.ensure_table()
        with session_scope() as session:
            return session.scalar(
                select(cls).where(cls.permission_group_name == permission_group_name)
            )

    @classmethod
    def get_all_permission_groups(cls):
        cls.ensure_table()
        with session_scope() as session:
            records = session.scalars(select(cls)).all()
            return [cls.to_dict(record) for record in records]

    @classmethod
    def add_permission_group(
        cls,
        permission_group_id: str,
        permission_group_name: str,
        access_rule_type: str = "exclude",
        access_rule_keys: List[str] = None,
        is_builtin: bool = False,
        other_info: Union[Dict, List] = None,
    ):
        permission_group_id = (permission_group_id or "").strip()
        permission_group_name = (permission_group_name or "").strip()
        access_rule = cls.normalize_access_rule(access_rule_type, access_rule_keys)

        cls.ensure_table()
        with session_scope() as session:
            if not (permission_group_id and permission_group_name):
                raise InvalidPermissionGroupError("权限分组信息不完整")
            if permission_group_id == AuthConfig.admin_role:
                raise InvalidPermissionGroupError("admin权限组不允许存储为数据库权限组")
            if permission_group_id in AuthConfig.roles:
                raise ExistingPermissionGroupError("权限分组id已存在")
            if permission_group_name in [
                item["description"] for item in AuthConfig.roles.values()
            ]:
                raise ExistingPermissionGroupError("权限分组名称已存在")
            if session.get(cls, permission_group_id):
                raise ExistingPermissionGroupError("权限分组id已存在")
            if session.scalar(
                select(cls).where(cls.permission_group_name == permission_group_name)
            ):
                raise ExistingPermissionGroupError("权限分组名称已存在")

            session.add(
                cls(
                    permission_group_id=permission_group_id,
                    permission_group_name=permission_group_name,
                    access_rule_type=access_rule["type"],
                    access_rule_keys=access_rule["keys"],
                    is_builtin=is_builtin,
                    other_info=other_info,
                )
            )

    @classmethod
    def upsert_permission_group(
        cls,
        permission_group_id: str,
        permission_group_name: str,
        access_rule_type: str = "exclude",
        access_rule_keys: List[str] = None,
        include_builtin: bool = False,
        other_info: Union[Dict, List] = None,
    ):
        """新增或更新权限分组，用于编辑有效权限组"""

        permission_group_id = (permission_group_id or "").strip()
        permission_group_name = (permission_group_name or "").strip()
        access_rule = cls.normalize_access_rule(access_rule_type, access_rule_keys)

        if not (permission_group_id and permission_group_name):
            raise InvalidPermissionGroupError("权限分组信息不完整")
        if permission_group_id == AuthConfig.admin_role:
            raise InvalidPermissionGroupError("admin权限组不允许编辑")
        if permission_group_id in AuthConfig.roles and not include_builtin:
            raise InvalidPermissionGroupError("硬编码权限组不允许通过新增操作覆盖")

        cls.ensure_table()
        with session_scope() as session:
            duplicate_group = session.scalar(
                select(cls).where(
                    (cls.permission_group_name == permission_group_name)
                    & (cls.permission_group_id != permission_group_id)
                )
            )
            if duplicate_group:
                raise ExistingPermissionGroupError("权限分组名称已存在")

            for role_id, role_info in AuthConfig.roles.items():
                if (
                    role_id != permission_group_id
                    and role_info["description"] == permission_group_name
                ):
                    raise ExistingPermissionGroupError("权限分组名称已存在")

            is_builtin = permission_group_id in AuthConfig.roles
            values = {
                "permission_group_name": permission_group_name,
                "access_rule_type": access_rule["type"],
                "access_rule_keys": access_rule["keys"],
                "is_builtin": is_builtin,
                "other_info": other_info,
            }
            if session.get(cls, permission_group_id):
                session.execute(
                    update(cls)
                    .where(cls.permission_group_id == permission_group_id)
                    .values(**values)
                )
            else:
                session.add(cls(permission_group_id=permission_group_id, **values))
            session.flush()
            return session.get(cls, permission_group_id)

    @classmethod
    def delete_permission_group(
        cls,
        permission_group_id: str,
        include_builtin: bool = False,
        ignore_user_reference: bool = False,
    ):
        permission_group_id = (permission_group_id or "").strip()
        if not permission_group_id:
            raise InvalidPermissionGroupError("权限分组信息不完整")

        cls.ensure_table()
        with session_scope() as session:
            match_group = session.get(cls, permission_group_id)
            if permission_group_id == AuthConfig.admin_role:
                raise InvalidPermissionGroupError("admin权限组不允许删除")
            if match_group and match_group.is_builtin and not include_builtin:
                raise InvalidPermissionGroupError("内置权限分组不允许删除")
            if (
                not ignore_user_reference
                and permission_group_id not in AuthConfig.roles
                and cls.get_permission_group_user_count(permission_group_id) > 0
            ):
                raise InvalidPermissionGroupError("权限分组已关联用户，不允许删除")

            result = session.execute(
                delete(cls).where(cls.permission_group_id == permission_group_id)
            )
            return result.rowcount or 0

    @classmethod
    def truncate_permission_groups(
        cls,
        execute: bool = False,
        include_builtin: bool = False,
        ignore_user_reference: bool = False,
    ):
        if execute:
            cls.ensure_table()
            with session_scope() as session:
                query = delete(cls)
                if not include_builtin:
                    query = query.where(cls.is_builtin.is_(False))
                if not ignore_user_reference:
                    from .users import Users

                    if Users.table_exists():
                        in_use_role_ids = session.scalars(
                            select(Users.user_role).distinct()
                        ).all()
                        query = query.where(
                            cls.permission_group_id.not_in(in_use_role_ids)
                        )
                session.execute(query)

    @classmethod
    def update_permission_group(
        cls,
        permission_group_id: str,
        include_builtin: bool = False,
        **kwargs,
    ):
        permission_group_id = (permission_group_id or "").strip()
        if not permission_group_id:
            raise InvalidPermissionGroupError("权限分组信息不完整")

        cls.ensure_table()
        with session_scope() as session:
            match_group = session.get(cls, permission_group_id)
            if not match_group:
                return None
            if permission_group_id == AuthConfig.admin_role:
                raise InvalidPermissionGroupError("admin权限组不允许编辑")
            if match_group.is_builtin and not include_builtin:
                raise InvalidPermissionGroupError("内置权限分组不允许编辑")

            kwargs.pop("permission_group_id", None)
            if "permission_group_name" in kwargs:
                permission_group_name = (kwargs["permission_group_name"] or "").strip()
                if not permission_group_name:
                    raise InvalidPermissionGroupError("权限分组信息不完整")
                duplicate_group = session.scalar(
                    select(cls).where(
                        (cls.permission_group_name == permission_group_name)
                        & (cls.permission_group_id != permission_group_id)
                    )
                )
                if duplicate_group:
                    raise ExistingPermissionGroupError("权限分组名称已存在")
                for role_id, role_info in AuthConfig.roles.items():
                    if (
                        role_id != permission_group_id
                        and role_info["description"] == permission_group_name
                    ):
                        raise ExistingPermissionGroupError("权限分组名称已存在")
                kwargs["permission_group_name"] = permission_group_name

            if "access_rule_type" in kwargs or "access_rule_keys" in kwargs:
                access_rule = cls.normalize_access_rule(
                    kwargs.get("access_rule_type", match_group.access_rule_type),
                    kwargs.get("access_rule_keys", match_group.access_rule_keys),
                )
                kwargs["access_rule_type"] = access_rule["type"]
                kwargs["access_rule_keys"] = access_rule["keys"]

            session.execute(
                update(cls)
                .where(cls.permission_group_id == permission_group_id)
                .values(**kwargs)
            )
            session.flush()
            return session.get(cls, permission_group_id)

    @classmethod
    def columns(cls):
        return [
            "permission_group_id",
            "permission_group_name",
            "access_rule_type",
            "access_rule_keys",
            "is_builtin",
            "other_info",
        ]

    @classmethod
    def to_dict(cls, record):
        return object_to_dict(record, cls.columns())
