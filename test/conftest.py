"""conftest.py is for test-suite-wide definitions

To run the tests locally, you'll need to pull the qoi test images. The original source
of these images was on Dominic Szablewski's qoiformat.org site, but I've mirrored them
so I'm not hogging his bandwidth.

Original URL (accesssed May 2022):
    https://qoiformat.org/qoi_test_images.zip

My mirrored URL (used in .github/workflows/test.yml)
    https://f000.backblazeb2.com/file/KerhinPublicBucket/qoi_test_images.zip

To pull and extract data so you can run it locally, run this from the project root:
    wget https://f000.backblazeb2.com/file/KerhinPublicBucket/qoi_test_images.zip
    unzip qoi_test_images.zip
"""
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-slow"):
        # --run-slow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(scope="session")
def test_image_root() -> Path:
    return Path(__file__).parent.parent / "qoi_test_images"
