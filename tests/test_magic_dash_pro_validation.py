import importlib.util
from pathlib import Path


def load_validation_utils():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "magic_dash"
        / "templates"
        / "magic-dash-pro"
        / "utils"
        / "validation_utils.py"
    )
    spec = importlib.util.spec_from_file_location(
        "magic_dash_pro_validation_utils", module_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validate_optional_email_accepts_empty_and_valid_values():
    validation_utils = load_validation_utils()

    assert validation_utils.validate_optional_email(None)
    assert validation_utils.validate_optional_email("")
    assert validation_utils.validate_optional_email(" admin@example.com ")
    assert validation_utils.validate_optional_email("user.name+tag@example.co.uk")


def test_validate_optional_email_rejects_invalid_values():
    validation_utils = load_validation_utils()

    assert not validation_utils.validate_optional_email("admin")
    assert not validation_utils.validate_optional_email("admin@example")
    assert not validation_utils.validate_optional_email("@example.com")
