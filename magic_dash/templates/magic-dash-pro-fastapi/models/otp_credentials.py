from ._registry import load_model
from . import db


OtpCredentials = load_model("otp_credentials", "OtpCredentials")

__all__ = ["OtpCredentials", "db"]
