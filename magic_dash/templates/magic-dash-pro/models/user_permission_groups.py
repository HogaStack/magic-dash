from ._registry import load_model
from . import db


UserPermissionGroups = load_model("user_permission_groups", "UserPermissionGroups")

__all__ = ["UserPermissionGroups", "db"]
