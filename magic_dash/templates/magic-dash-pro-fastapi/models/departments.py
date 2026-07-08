from ._registry import load_model
from . import db


Departments = load_model("departments", "Departments")

__all__ = ["Departments", "db"]
