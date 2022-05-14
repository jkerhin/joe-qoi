from pathlib import Path

from setuptools import setup

version = Path("./joe_qoi/version.py").read_text().split("=")[1].replace('"', "")


setup(
    name="joe-qoi",
    description="Pure Python implementation of QOI image format",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    author="Joe Kerhin",
    url="https://github.com/jkerhin/joe-qoi",
    project_urls={
        "Issues": "https://github.com/jkerhin/joe-qoi/issues",
        "CI": "https://github.com/jkerhin/joe-qoi/actions",
        "Changelog": "https://github.com/jkerhin/joe-qoi/releases",
    },
    license="MIT",
    version=version,
    packages=["joe_qoi"],
    install_requires=[],
    extras_require={"test": ["pytest"]},
    python_requires=">=3.7",
)
