import pytest

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
    expected_byte = b"\x4b"  # b0100 1011
    assert expected_byte == packed_diff


@pytest.mark.parametrize("second_rgb", [(0, 5, 5), (5, 0, 5), (0, 0, 5), (10, 50, 5)])
def test_pack_diff_out_of_range(second_rgb):
    px1 = RgbaPixel(5, 5, 5)
    px2 = RgbaPixel(*second_rgb)
    with pytest.raises(ValueError) as e:
        _ = QoiEncoder.pack_diff(px1, px2)
    assert str(e.value) == "QOI_OP_DIFF all deltas must be in range [-2, 1]"
