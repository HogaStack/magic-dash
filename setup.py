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
    homepage="https://github.com/CNFeffery/magic-dash",
    author="CNFeffery <fefferypzy@gmail.com>",
    packages=find_packages(),
    license="MIT",
    description="A command-line tool for quickly generating standard Dash application projects.",
    long_description=io.open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Framework :: Dash",
    ],
    url="https://github.com/CNFeffery/magic-dash",
    python_requires=">=3.8, <3.14",
    install_requires=["click"],
    entry_points={
        "console_scripts": [
            "magic-dash = magic_dash:magic_dash",
        ],
    },
    include_package_data=True,
)
