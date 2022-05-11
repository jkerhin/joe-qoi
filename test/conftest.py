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


@pytest.fixture(scope="session")
def test_image_root() -> Path:
    return Path(__file__).parent.parent / "qoi_test_images"
