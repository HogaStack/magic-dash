from peewee import BooleanField, CharField
from typing import Union, Dict, List
from playhouse.sqlite_ext import JSONField

from . import db, BaseModel
from .exceptions import InvalidPermissionGroupError, ExistingPermissionGroupError
from configs import AuthConfig, RouterConfig


class UserPermissionGroups(BaseModel):
    """用户权限分组表模型类"""

    # 权限分组id，主键，对应Users.user_role
    permission_group_id = CharField(primary_key=True)

    # 权限分组展示名称，唯一
    permission_group_name = CharField(unique=True)

    # 页面访问规则类型，可选值：all/include/exclude
    access_rule_type = CharField(default="exclude")

    # 页面访问规则key列表，对应RouterConfig.core_side_menu中的菜单项key
    access_rule_keys = JSONField(null=True)

    # 是否为内置权限分组
    is_builtin = BooleanField(default=False)

    # 权限分组其他辅助信息，任意JSON格式，允许空值
    other_info = JSONField(null=True)

    @classmethod
    def ensure_table(cls):
        """确保用户权限分组表存在，用于兼容已初始化过的旧数据库"""

        with db.connection_context():
            if not cls.table_exists():
                db.create_tables([cls])

            # admin权限组只允许通过硬编码配置定义，清理任何历史遗留的同id数据库记录。
            cls.delete().where(cls.permission_group_id == AuthConfig.admin_role).execute()

    @classmethod
    def normalize_access_rule(
        cls,
        access_rule_type: str = "exclude",
        access_rule_keys: List[str] = None,
    ):
        """标准化并校验页面访问规则"""

        if access_rule_type not in ["all", "include", "exclude"]:
            raise InvalidPermissionGroupError("权限规则类型不正确")

        if access_rule_type == "all":
            return {
                "type": access_rule_type,
                "keys": [],
            }

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

        return {
            "type": access_rule_type,
            "keys": access_rule_keys,
        }

    @staticmethod
    def get_valid_access_rule_keys():
        """获取数据库权限规则允许引用的有效页面key集合"""

        return {
            pathname
            for pathname in RouterConfig.valid_pathnames
            if isinstance(pathname, str) and pathname not in RouterConfig.public_pathnames
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

            # 配置参数中的硬编码角色已合并，不重复追加
            if permission_group_id in effective_roles:
                continue

            # 数据库权限组名称若与硬编码权限组名称冲突，则不纳入有效角色
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
        """获取硬编码权限组名称列表"""

        return [
            role_info["description"]
            for role_id, role_info in AuthConfig.roles.items()
            if role_id != exclude_role_id
        ]

    @classmethod
    def get_permission_group_conflict(cls, permission_group: dict):
        """获取数据库权限组与硬编码权限组之间的冲突信息"""

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
            if permission_group_id in AuthConfig.roles:
                return {
                    "type": "config_name_conflict",
                    "label": "名称冲突",
                    "message": "同id数据库覆盖记录名称与其他硬编码权限组冲突，已忽略该覆盖记录，当前权限组继续以硬编码配置为准。",
                }

            return {
                "type": "config_name_conflict",
                "label": "名称冲突",
                "message": "数据库权限组名称与硬编码权限组名称冲突，已从有效角色中排除。",
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

        return {
            "type": None,
            "label": "正常",
            "message": None,
        }

    @staticmethod
    def format_access_rule_keys(access_rule_keys: List = None):
        """格式化页面访问规则key列表，用于表格展示"""

        if not access_rule_keys:
            return []

        return [
            item.pattern if hasattr(item, "pattern") else item
            for item in access_rule_keys
        ]

    @classmethod
    def get_effective_role_options(cls):
        """获取配置参数与数据库综合后的有效用户角色选项"""

        return [
            {
                "label": role_info["description"],
                "value": role_id,
            }
            for role_id, role_info in cls.get_effective_roles().items()
        ]

    @classmethod
    def get_role_description(cls, permission_group_id: str, default: str = "未知角色"):
        """获取有效用户角色展示名称"""

        return cls.get_effective_roles().get(
            permission_group_id,
            {},
        ).get("description", default)

    @classmethod
    def is_role_valid(cls, permission_group_id: str):
        """判断用户角色是否属于配置参数或数据库定义的有效角色"""

        return permission_group_id in cls.get_effective_roles()

    @classmethod
    def get_permission_group_user_count(cls, permission_group_id: str):
        """获取指定权限分组关联的用户数量"""

        permission_group_id = (permission_group_id or "").strip()
        if not permission_group_id:
            return 0

        from .users import Users

        with db.connection_context():
            if not Users.table_exists():
                return 0

            return Users.select().where(Users.user_role == permission_group_id).count()

    @classmethod
    def get_effective_pathname_access_rule(cls, permission_group_id: str):
        """获取配置参数与数据库综合后的页面访问规则"""

        match_group = cls.get_permission_group(permission_group_id)

        # admin角色始终使用配置参数中的底层硬编码规则
        if permission_group_id == AuthConfig.admin_role:
            return AuthConfig.pathname_access_rules.get(permission_group_id)

        # 其他配置参数角色可由数据库记录覆盖
        if permission_group_id in AuthConfig.roles:
            if match_group and cls.get_permission_group_conflict(
                {
                    "permission_group_id": match_group.permission_group_id,
                    "permission_group_name": match_group.permission_group_name,
                    "access_rule_type": match_group.access_rule_type,
                    "access_rule_keys": match_group.access_rule_keys,
                }
            )["type"] == "config_override":
                return cls.normalize_access_rule(
                    match_group.access_rule_type,
                    match_group.access_rule_keys,
                )
            return AuthConfig.pathname_access_rules.get(permission_group_id)

        if not match_group:
            return None

        if cls.get_permission_group_conflict(
            {
                "permission_group_id": match_group.permission_group_id,
                "permission_group_name": match_group.permission_group_name,
                "access_rule_type": match_group.access_rule_type,
                "access_rule_keys": match_group.access_rule_keys,
            }
        )["type"]:
            return None

        return cls.normalize_access_rule(
            match_group.access_rule_type,
            match_group.access_rule_keys,
        )

    @classmethod
    def get_effective_pathname_access_rules(cls):
        """获取配置参数与数据库综合后的全部页面访问规则"""

        effective_rules = {}

        for permission_group_id in AuthConfig.roles:
            effective_rules[permission_group_id] = (
                cls.get_effective_pathname_access_rule(permission_group_id)
            )

        for permission_group in cls.get_all_permission_groups():
            permission_group_id = permission_group["permission_group_id"]

            # 配置参数中的硬编码角色已合并，不重复追加
            if permission_group_id in effective_rules:
                continue

            # 数据库权限组若与硬编码权限组名称冲突，则不纳入有效权限规则
            if cls.get_permission_group_conflict(permission_group)["type"]:
                continue

            effective_rules[permission_group_id] = cls.normalize_access_rule(
                permission_group["access_rule_type"],
                permission_group["access_rule_keys"],
            )

        return effective_rules

    @classmethod
    def get_effective_permission_group_records(cls):
        """获取配置参数与数据库综合后的有效权限分组记录"""

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
                    "permission_group_name": permission_group[
                        "permission_group_name"
                    ],
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
        """根据权限分组id查询权限分组信息"""

        permission_group_id = (permission_group_id or "").strip()
        if not permission_group_id:
            return None

        cls.ensure_table()
        with db.connection_context():
            return cls.get_or_none(cls.permission_group_id == permission_group_id)

    @classmethod
    def get_permission_group_by_name(cls, permission_group_name: str):
        """根据权限分组展示名称查询权限分组信息"""

        permission_group_name = (permission_group_name or "").strip()
        if not permission_group_name:
            return None

        cls.ensure_table()
        with db.connection_context():
            return cls.get_or_none(cls.permission_group_name == permission_group_name)

    @classmethod
    def get_all_permission_groups(cls):
        """获取所有用户权限分组信息"""

        cls.ensure_table()
        with db.connection_context():
            return list(cls.select().dicts())

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
        """添加用户权限分组"""

        permission_group_id = (permission_group_id or "").strip()
        permission_group_name = (permission_group_name or "").strip()
        access_rule = cls.normalize_access_rule(access_rule_type, access_rule_keys)

        cls.ensure_table()
        with db.connection_context():
            # 若必要权限分组信息不完整
            if not (permission_group_id and permission_group_name):
                raise InvalidPermissionGroupError("权限分组信息不完整")

            # admin权限组只允许通过硬编码配置定义
            elif permission_group_id == AuthConfig.admin_role:
                raise InvalidPermissionGroupError("admin权限组不允许存储为数据库权限组")

            # 若权限分组id与硬编码权限组冲突
            elif permission_group_id in AuthConfig.roles:
                raise ExistingPermissionGroupError("权限分组id已存在")

            # 若权限分组展示名称与硬编码权限组冲突
            elif permission_group_name in [
                item["description"] for item in AuthConfig.roles.values()
            ]:
                raise ExistingPermissionGroupError("权限分组名称已存在")

            # 若权限分组id已存在
            elif cls.get_or_none(cls.permission_group_id == permission_group_id):
                raise ExistingPermissionGroupError("权限分组id已存在")

            # 若权限分组展示名称存在重复
            elif cls.get_or_none(cls.permission_group_name == permission_group_name):
                raise ExistingPermissionGroupError("权限分组名称已存在")

            # 执行权限分组添加操作
            with db.atomic():
                cls.create(
                    permission_group_id=permission_group_id,
                    permission_group_name=permission_group_name,
                    access_rule_type=access_rule["type"],
                    access_rule_keys=access_rule["keys"],
                    is_builtin=is_builtin,
                    other_info=other_info,
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
        """新增或更新用户权限分组，用于编辑有效权限组"""

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
        with db.connection_context():
            duplicate_group = cls.get_or_none(
                (cls.permission_group_name == permission_group_name)
                & (cls.permission_group_id != permission_group_id)
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

            with db.atomic():
                if cls.get_or_none(cls.permission_group_id == permission_group_id):
                    cls.update(
                        permission_group_name=permission_group_name,
                        access_rule_type=access_rule["type"],
                        access_rule_keys=access_rule["keys"],
                        is_builtin=is_builtin,
                        other_info=other_info,
                    ).where(
                        cls.permission_group_id == permission_group_id
                    ).execute()
                else:
                    cls.create(
                        permission_group_id=permission_group_id,
                        permission_group_name=permission_group_name,
                        access_rule_type=access_rule["type"],
                        access_rule_keys=access_rule["keys"],
                        is_builtin=is_builtin,
                        other_info=other_info,
                    )

            return cls.get_or_none(cls.permission_group_id == permission_group_id)

    @classmethod
    def delete_permission_group(
        cls,
        permission_group_id: str,
        include_builtin: bool = False,
        ignore_user_reference: bool = False,
    ):
        """删除用户权限分组"""

        permission_group_id = (permission_group_id or "").strip()
        if not permission_group_id:
            raise InvalidPermissionGroupError("权限分组信息不完整")

        cls.ensure_table()
        with db.connection_context():
            match_group = cls.get_or_none(cls.permission_group_id == permission_group_id)
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

            with db.atomic():
                return (
                    cls.delete()
                    .where(cls.permission_group_id == permission_group_id)
                    .execute()
                )

    @classmethod
    def truncate_permission_groups(
        cls,
        execute: bool = False,
        include_builtin: bool = False,
        ignore_user_reference: bool = False,
    ):
        """清空用户权限分组，请小心使用"""

        # 若保险参数execute=True
        if execute:
            cls.ensure_table()
            with db.connection_context():
                with db.atomic():
                    query = cls.delete()
                    if not include_builtin:
                        query = query.where(cls.is_builtin == False)  # noqa: E712
                    if not ignore_user_reference:
                        from .users import Users

                        if Users.table_exists():
                            in_use_role_ids = [
                                item["user_role"]
                                for item in Users.select(Users.user_role)
                                .distinct()
                                .dicts()
                            ]
                            query = query.where(
                                cls.permission_group_id.not_in(in_use_role_ids)
                            )
                    query.execute()

    @classmethod
    def update_permission_group(
        cls,
        permission_group_id: str,
        include_builtin: bool = False,
        **kwargs,
    ):
        """更新用户权限分组信息"""

        permission_group_id = (permission_group_id or "").strip()
        if not permission_group_id:
            raise InvalidPermissionGroupError("权限分组信息不完整")

        cls.ensure_table()
        with db.connection_context():
            match_group = cls.get_or_none(cls.permission_group_id == permission_group_id)
            if not match_group:
                return None

            if permission_group_id == AuthConfig.admin_role:
                raise InvalidPermissionGroupError("admin权限组不允许编辑")

            if match_group.is_builtin and not include_builtin:
                raise InvalidPermissionGroupError("内置权限分组不允许编辑")

            if "permission_group_id" in kwargs:
                kwargs.pop("permission_group_id")

            if "permission_group_name" in kwargs:
                permission_group_name = (kwargs["permission_group_name"] or "").strip()
                if not permission_group_name:
                    raise InvalidPermissionGroupError("权限分组信息不完整")

                duplicate_group = cls.get_or_none(
                    (cls.permission_group_name == permission_group_name)
                    & (cls.permission_group_id != permission_group_id)
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

            if (
                "access_rule_type" in kwargs
                or "access_rule_keys" in kwargs
            ):
                access_rule = cls.normalize_access_rule(
                    kwargs.get("access_rule_type", match_group.access_rule_type),
                    kwargs.get("access_rule_keys", match_group.access_rule_keys),
                )
                kwargs["access_rule_type"] = access_rule["type"]
                kwargs["access_rule_keys"] = access_rule["keys"]

            with db.atomic():
                cls.update(**kwargs).where(
                    cls.permission_group_id == permission_group_id
                ).execute()

            # 返回成功更新后的用户权限分组信息
            return cls.get_or_none(cls.permission_group_id == permission_group_id)
