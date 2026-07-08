from typing import Dict, List, Union

from sqlalchemy import JSON, String, delete, select, update
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel, object_to_dict, session_scope
from ..exceptions import ExistingDepartmentError, InvalidDepartmentError
from ..schema_contract import TABLE_NAMES


class Departments(BaseModel):
    """SQLAlchemy版部门信息表模型"""

    __tablename__ = TABLE_NAMES["Departments"]

    department_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    department_name: Mapped[str] = mapped_column(String(255), unique=True)
    parent_department_id: Mapped[str] = mapped_column(String(255), nullable=True)
    other_info: Mapped[object] = mapped_column(JSON, nullable=True)

    @classmethod
    def get_department(cls, department_id: str):
        with session_scope() as session:
            return session.get(cls, department_id)

    @classmethod
    def get_children_departments(cls, department_id: str):
        with session_scope() as session:
            records = session.scalars(
                select(cls).where(cls.parent_department_id == department_id)
            ).all()
            return [object_to_dict(record, cls.columns()) for record in records]

    @classmethod
    def get_department_by_name(cls, department_name: str):
        with session_scope() as session:
            return session.scalar(
                select(cls).where(cls.department_name == department_name)
            )

    @classmethod
    def get_all_departments(cls):
        """获取全部部门信息，返回普通字典列表以适配界面表格"""

        with session_scope() as session:
            records = session.scalars(select(cls)).all()
            return [object_to_dict(record, cls.columns()) for record in records]

    @classmethod
    def add_department(
        cls,
        department_id: str,
        department_name: str,
        parent_department_id: str = None,
        other_info: Union[Dict, List] = None,
    ):
        with session_scope() as session:
            if not (department_id and department_name):
                raise InvalidDepartmentError("部门信息不完整")
            if session.get(cls, department_id):
                raise ExistingDepartmentError("部门id已存在")
            if session.scalar(
                select(cls).where(cls.department_name == department_name)
            ):
                raise ExistingDepartmentError("部门名已存在")

            session.add(
                cls(
                    department_id=department_id,
                    department_name=department_name,
                    parent_department_id=parent_department_id,
                    other_info=other_info,
                )
            )

    @classmethod
    def delete_department(cls, department_id: str):
        """删除部门及其全部后代部门"""

        with session_scope() as session:

            def get_descendant_ids(dept_id: str) -> list:
                ids = [dept_id]
                child_ids = session.scalars(
                    select(cls.department_id).where(cls.parent_department_id == dept_id)
                ).all()
                for child_id in child_ids:
                    ids.extend(get_descendant_ids(child_id))
                return ids

            session.execute(
                delete(cls).where(
                    cls.department_id.in_(get_descendant_ids(department_id))
                )
            )

    @classmethod
    def truncate_departments(cls, execute: bool = False):
        if execute:
            with session_scope() as session:
                session.execute(delete(cls))

    @classmethod
    def update_department(cls, department_id: str, **kwargs):
        with session_scope() as session:
            session.execute(
                update(cls).where(cls.department_id == department_id).values(**kwargs)
            )
            session.flush()
            return session.get(cls, department_id)

    @classmethod
    def columns(cls):
        return [
            "department_id",
            "department_name",
            "parent_department_id",
            "other_info",
        ]
