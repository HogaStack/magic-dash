from ._registry import load_model
from . import db


Users = load_model("users", "Users")

__all__ = ["Users", "db"]
