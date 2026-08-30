import subprocess
import sys
from pathlib import Path

import pytest


TEMPLATES_ROOT = Path(__file__).resolve().parents[1] / "magic_dash" / "templates"
CONTRACT_RUNNER = Path(__file__).with_name("_magic_dash_pro_orm_contract.py")


@pytest.mark.parametrize(
    "template_name",
    ["magic-dash-pro", "magic-dash-pro-fastapi"],
)
@pytest.mark.parametrize("orm_engine", ["peewee", "sqlalchemy", "sqlmodel"])
def test_magic_dash_pro_engine_keeps_model_api_contract(
    tmp_path,
    template_name,
    orm_engine,
):
    result = subprocess.run(
        [
            sys.executable,
            str(CONTRACT_RUNNER),
            str(TEMPLATES_ROOT / template_name),
            orm_engine,
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"{template_name}/{orm_engine} contract check failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
