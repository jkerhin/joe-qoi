import pytest
from PIL import Image

from joe_qoi import QoiDecoder


def test_decode_header_good():
    test_bytes = bytes.fromhex("716f 6966 0000 0320 0000 0258 0400")  # dice.qoi
    width, height, has_alpha, all_linear = QoiDecoder.decode_header(test_bytes)
    assert width == 800
    assert height == 600
    assert has_alpha is True
    assert all_linear is False


def test_decode_header_bad():
    test_bytes = b"\xFF" * 14
    with pytest.raises(ValueError) as e:
        _ = QoiDecoder.decode_header(test_bytes, validate=True)
    assert str(e.value) == "Magic bytes incorrect"


@pytest.mark.parametrize(
    "base_name",
    [
        "dice",
        "kodim10",
        "kodim23",
        "qoi_logo",
        "testcard",
        "testcard_rgba",
        "wikipedia_008",
    ],
)
def test_decode_against_png(test_image_root, base_name):
    png_pth = test_image_root / f"{base_name}.png"
    qoi_pth = test_image_root / f"{base_name}.qoi"
    png_bytes = Image.open(png_pth).tobytes()
    qd = QoiDecoder.from_file(qoi_pth)
    if qd.has_alpha:
        qoi_bytes = b"".join((px.packed_rgba for px in qd.pixels))
    else:
        qoi_bytes = b"".join((px.packed_rgb for px in qd.pixels))
    assert qoi_bytes == png_bytes
