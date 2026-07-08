from ._registry import load_model
from . import db


LoginLogs = load_model("logs", "LoginLogs")

__all__ = ["LoginLogs", "db"]
