import io
import os
import re
from setuptools import setup, find_packages


def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "magic_dash", "__init__.py")
    with open(version_file, encoding="utf-8") as f:
        match = re.search(r'__version__ = "([^"]+)"', f.read())
        if not match:
            raise RuntimeError("无法找到版本号")
        return match.group(1)


setup(
    name="magic_dash",
    version=get_version(),
    author_email="fefferypzy@gmail.com",
    homepage="https://github.com/HogaStack/magic-dash",
    author="HogaStack <fefferypzy@gmail.com>",
    packages=find_packages(),
    license="MIT",
    description="A command-line tool for quickly generating standard Dash application projects.",
    long_description=io.open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Framework :: Dash",
    ],
    url="https://github.com/HogaStack/magic-dash",
    python_requires=">=3.9, <3.15",
    install_requires=["click", "rich", "questionary", "dash>=4.2.0,<5.0.0"],
    extras_require={
        "test": [
            "pytest",
            "peewee>=4.0.0",
            "SQLAlchemy>=2.0.0",
            "sqlmodel>=0.0.27",
        ],
    },
    entry_points={
        "console_scripts": [
            "magic-dash = magic_dash:magic_dash",
        ],
    },
    include_package_data=True,
)
