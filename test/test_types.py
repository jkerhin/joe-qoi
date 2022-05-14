from joe_qoi.types import RgbaPixel, SignedChar


def test_pack_rgb():
    px = RgbaPixel(r=10, g=100, b=200)
    expected_bytes = bytes.fromhex("0A 64 C8")
    packed = px.packed_rgb
    assert expected_bytes == packed


def test_pack_rgba():
    px = RgbaPixel(r=10, g=100, b=200, a=50)
    expected_bytes = bytes.fromhex("0A 64 C8 32")
    packed = px.packed_rgba
    assert expected_bytes == packed


def test_signedchar_high():
    expected = -126
    sc = SignedChar(130)
    assert sc == expected


def test_signedchar_low():
    expected = 126
    sc = SignedChar(-130)
    assert sc == expected


def test_signedchar_add():
    expected = -126
    test = SignedChar(120) + 10
    assert isinstance(test, SignedChar)
    assert test == expected


def test_signedchar_sub():
    expected = 126
    test = SignedChar(-120) - 10
    assert isinstance(test, SignedChar)
    assert test == expected
