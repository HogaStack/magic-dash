from peewee import CharField
from typing import Union, Dict, List
from playhouse.sqlite_ext import JSONField

from . import db, BaseModel
from .exceptions import InvalidDepartmentError, ExistingDepartmentError


class Departments(BaseModel):
    """部门信息表模型类"""

    # 部门id，主键
    department_id = CharField(primary_key=True)

    # 部门名称，唯一
    department_name = CharField(unique=True)

    # 所属部门id，允许空值
    parent_department_id = CharField(null=True)

    # 部门其他辅助信息，任意JSON格式，允许空值
    other_info = JSONField(null=True)

    @classmethod
    def get_department(cls, department_id: str):
        """根据部门id查询部门信息"""

        with db.connection_context():
            return cls.get_or_none(cls.department_id == department_id)

    @classmethod
    def get_department_by_name(cls, department_name: str):
        """根据部门名称查询部门信息"""

        with db.connection_context():
            return cls.get_or_none(cls.department_name == department_name)

    @classmethod
    def get_all_departments(cls):
        """获取所有部门信息"""

        with db.connection_context():
            return list(cls.select().dicts())

    @classmethod
    def add_department(
        cls,
        department_id: str,
        department_name: str,
        parent_department_id: str = None,
        other_info: Union[Dict, List] = None,
    ):
        """添加部门"""

        with db.connection_context():
            # 若必要部门信息不完整
            if not (department_id and department_name):
                raise InvalidDepartmentError("部门信息不完整")

            # 若部门id已存在
            elif cls.get_or_none(cls.department_id == department_id):
                raise ExistingDepartmentError("部门id已存在")

            # 若部门名存在重复
            elif cls.get_or_none(cls.department_name == department_name):
                raise ExistingDepartmentError("部门名已存在")

            # 执行部门添加操作
            with db.atomic():
                cls.create(
                    department_id=department_id,
                    department_name=department_name,
                    parent_department_id=parent_department_id,
                    other_info=other_info,
                )

    @classmethod
    def delete_department(cls, department_id: str):
        """删除部门"""

        with db.connection_context():
            with db.atomic():
                cls.delete().where(cls.department_id == department_id).execute()

    @classmethod
    def truncate_departments(cls, execute: bool = False):
        """清空部门，请小心使用"""

        # 若保险参数execute=True
        if execute:
            with db.connection_context():
                with db.atomic():
                    cls.delete().execute()

    @classmethod
    def update_department(cls, department_id: str, **kwargs):
        """更新部门信息"""

        with db.connection_context():
            with db.atomic():
                cls.update(**kwargs).where(cls.department_id == department_id).execute()

            # 返回成功更新后的部门信息
            return cls.get_or_none(cls.department_id == department_id)
