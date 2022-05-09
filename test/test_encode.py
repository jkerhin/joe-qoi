from joe_qoi import QoiEncoder


def test_encode_header():
    test_bytes = bytes.fromhex("716f 6966 0000 0320 0000 0258 0400")  # dice.qoi
    header_bytes = QoiEncoder.encode_header(800, 600, True, False)
    assert test_bytes == header_bytes
