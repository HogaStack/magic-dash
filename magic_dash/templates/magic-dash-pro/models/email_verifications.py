from ._registry import load_model
from . import db


EmailVerifications = load_model("email_verifications", "EmailVerifications")

__all__ = ["EmailVerifications", "db"]
