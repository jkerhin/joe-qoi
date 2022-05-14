import pytest
from PIL import Image

from joe_qoi.codecs import QoiEncoder, RgbaPixel


def test_encode_header():
    expected_bytes = bytes.fromhex("716f 6966 0000 0320 0000 0258 0400")  # dice.qoi
    header_bytes = QoiEncoder.encode_header(800, 600, True, False)
    assert expected_bytes == header_bytes


def test_pack_rgb():
    px = RgbaPixel(r=10, g=100, b=200)
    expected_bytes = bytes.fromhex("FE 0A 64 C8")
    packed = QoiEncoder.pack_rgb(px)
    assert expected_bytes == packed


def test_pack_rgba():
    px = RgbaPixel(r=10, g=100, b=200, a=50)
    expected_bytes = bytes.fromhex("FF 0A 64 C8 32")
    packed = QoiEncoder.pack_rgba(px)
    assert expected_bytes == packed


def test_pack_index():
    packed_ix = QoiEncoder.pack_index(50)
    expected_byte = b"\x32"
    assert expected_byte == packed_ix


@pytest.mark.parametrize("index", [64, -1])
def test_pack_index_out_of_range(index):
    with pytest.raises(ValueError) as e:
        _ = QoiEncoder.pack_index(index)
    assert str(e.value) == "QOI_OP_INDEX allowed range is [0, 63]"


def test_pack_diff():
    prev_px = RgbaPixel(5, 5, 5)
    this_px = RgbaPixel(3, 5, 6)
    packed_diff = QoiEncoder.pack_diff(prev_px, this_px)
    expected_byte = b"\x4b"  # b0100 1011
    assert expected_byte == packed_diff


def test_pack_diff_wraparound():
    prev_px = RgbaPixel(255, 2, 255)
    this_px = RgbaPixel(253, 1, 0)
    packed_diff = QoiEncoder.pack_diff(prev_px, this_px)
    expected_byte = b"\x47"  # b0100 0111
    assert expected_byte == packed_diff


@pytest.mark.parametrize("second_rgb", [(0, 5, 5), (5, 0, 5), (0, 0, 5), (10, 50, 5)])
def test_pack_diff_out_of_range(second_rgb):
    px1 = RgbaPixel(5, 5, 5)
    px2 = RgbaPixel(*second_rgb)
    with pytest.raises(ValueError) as e:
        _ = QoiEncoder.pack_diff(px1, px2)
    assert str(e.value) == "QOI_OP_DIFF all deltas must be in range [-2, 1]"


def test_pack_luma():
    prev_px = RgbaPixel(100, 100, 100)
    this_px = RgbaPixel(115, 120, 125)
    packed_luma = QoiEncoder.pack_luma(prev_px, this_px)
    expected_bytes = b"\xB4\x3D"  # b1011 0100  0011 1101
    assert expected_bytes == packed_luma


def test_pack_luma_wraparound():
    prev_px = RgbaPixel(250, 250, 250)
    this_px = RgbaPixel(251, 1, 8)
    packed_luma = QoiEncoder.pack_luma(prev_px, this_px)
    expected_bytes = b"\xA7\x2F"  # b1011 0100  0010 1111
    assert expected_bytes == packed_luma


@pytest.mark.parametrize(
    "second_rgb,expected_err_str",
    [
        ((150, 150, 150), "QOI_OP_LUMA green delta must be in range [-32, 31]"),
        ((0, 0, 0), "QOI_OP_LUMA green delta must be in range [-32, 31]"),
        (
            (110, 120, 120),
            "QOI_OP_LUMA red, blue offsets from green must be in range [-8, 7]",
        ),
        (
            (70, 70, 80),
            "QOI_OP_LUMA red, blue offsets from green must be in range [-8, 7]",
        ),
    ],
)
def test_pack_luma_out_of_range(second_rgb, expected_err_str):
    px1 = RgbaPixel(100, 100, 100)
    px2 = RgbaPixel(*second_rgb)
    with pytest.raises(ValueError) as e:
        _ = QoiEncoder.pack_luma(px1, px2)
    assert str(e.value) == expected_err_str


def test_pack_run():
    packed_run = QoiEncoder.pack_run(50)
    expected_byte = b"\xF1"
    assert expected_byte == packed_run


@pytest.mark.parametrize("count", [63, 0])
def test_pack_run_out_of_range(count):
    with pytest.raises(ValueError) as e:
        _ = QoiEncoder.pack_run(count)
    assert str(e.value) == "QOI_OP_RUN allowed range is [1, 62]"


@pytest.mark.slow
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
    qoi_bytes = qoi_pth.read_bytes()

    im = Image.open(png_pth)
    qe = QoiEncoder.from_bytes(
        im.tobytes(),
        width=im.width,
        height=im.height,
        has_alpha="A" in im.mode,  # RGB / RGBA
        all_linear=False,  # False in all test images
    )
    assert bytes(qe) == qoi_bytes
