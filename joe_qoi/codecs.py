"""Encoding and Decoding operations for QOI format"""
import struct
from typing import Tuple


class QoiEncoder:
    def __init__(self):
        pass


class QoiDecoder:
    def __init__(self, qoi_data: bytes):
        self.qoi_data = qoi_data
        self._ix = 0
        self.width, self.height, self.has_alpha, self.all_linear = self._read_header()

    def __repr__(self):
        len_packed = len(self.qoi_data)
        resolution = f"{self.width}x{self.height}"
        channel_str = "RGBA" if self.has_alpha else "RGB"
        colorspace_str = (
            "all channels linear" if self.all_linear else "sRGB with linear alpha"
        )
        return (
            f"{resolution} {channel_str}, {colorspace_str}, {len_packed} bytes packed"
        )

    def _read_header(self):
        header_bytes = self.qoi_data[:14]
        width, height, has_alpha, all_linear = self.decode_header(
            header_bytes, validate=True
        )
        self._ix = 14
        return width, height, has_alpha, all_linear

    @staticmethod
    def decode_header(
        header_bytes: bytes, validate: bool = False
    ) -> Tuple[int, int, bool, bool]:
        """From the spec document:

        A QOI file has a 14 byte header, followed by any number of data "chunks" and an
        8-byte end marker.
        struct qoi_header_t {
            char     magic[4];   // magic bytes "qoif"
            uint32_t width;      // image width in pixels (BE)
            uint32_t height;     // image height in pixels (BE)
            uint8_t  channels;   // 3 = RGB, 4 = RGBA
            uint8_t  colorspace; // 0 = sRGB with linear alpha, 1 = all channels linear
        };

        """
        if validate and (header_bytes[:4] != b"qoif"):
            raise ValueError("Magic bytes incorrect")

        width, height = struct.unpack_from(">II", header_bytes, offset=4)
        channels, colorspace = struct.unpack_from(">BB", header_bytes, offset=12)
        if validate and (channels not in {3, 4}):
            raise ValueError(
                f"Incorrect number of channels! Allowed [3, 4] Actual: {channels}"
            )
        if validate and (colorspace not in {0, 1}):
            raise ValueError(
                f"Incorrect colorspace! Allowed [0, 1] Actual: {colorspace}"
            )
        has_alpha = channels == 4
        all_linear = colorspace == 1
        return width, height, has_alpha, all_linear

    @classmethod
    def from_file(cls, file_name: str):
        with open(file_name, "rb") as hdl:
            data = hdl.read()
        return cls(data)
