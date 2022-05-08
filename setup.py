import os

from setuptools import setup

VERSION = "0.1"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="joe-qoi",
    description="Pure Python implementation of QOI image format",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Joe Kerhin",
    url="https://github.com/jkerhin/joe-qoi",
    project_urls={
        "Issues": "https://github.com/jkerhin/joe-qoi/issues",
        "CI": "https://github.com/jkerhin/joe-qoi/actions",
        "Changelog": "https://github.com/jkerhin/joe-qoi/releases",
    },
    license="MIT",
    version=VERSION,
    packages=["joe_qoi"],
    install_requires=[],
    extras_require={"test": ["pytest"]},
    python_requires=">=3.7",
)
