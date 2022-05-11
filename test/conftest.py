from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_image_root() -> Path:
    return Path(__file__).parent.parent / "qoi_test_images"
