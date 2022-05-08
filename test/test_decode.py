from tkinter import W

from pytest import raises

from joe_qoi import QoiDecoder


def test_decode_header_good():
    test_bytes = bytes.fromhex("716f 6966 0000 0320 0000 0258 0400")  # dice.qoi
    width, height, has_alpha, all_linear = QoiDecoder.decode_header(test_bytes)
    assert width == 800
    assert height == 600
    assert has_alpha == True
    assert all_linear == False


def test_decode_header_bad():
    test_bytes = b"\xFF" * 14
    with raises(ValueError) as e:
        _ = QoiDecoder.decode_header(test_bytes, validate=True)
    assert str(e.value) == "Magic bytes incorrect"
