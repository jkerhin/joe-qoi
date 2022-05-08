"""Encoding and Decoding operations for QOI format"""
import logging
import struct
from copy import copy
from dataclasses import dataclass
from typing import Tuple

log = logging.getLogger(__name__)
# fmt: off
QOI_OP_INDEX = int("00", 16)  # b00xxxxxxxx
QOI_OP_DIFF  = int("40", 16)  # b01xxxxxxxx
QOI_OP_LUMA  = int("80", 16)  # b10xxxxxxxx
QOI_OP_RUN   = int("C0", 16)  # b11xxxxxxxx
QOI_MASK_2   = int("C0", 16)  # b11xxxxxxxx
# fmt: on


@dataclass
class RgbPixel:
    r: int = 0
    g: int = 0
    b: int = 0


@dataclass
class RgbaPixel:
    r: int = 0
    g: int = 0
    b: int = 0
    a: int = 0


class QoiEncoder:
    def __init__(self):
        pass


class QoiDecoder:
    def __init__(self, qoi_data: bytes):
        self.qoi_data = qoi_data
        self._ix = 0
        self._len = len(qoi_data)

        self.width, self.height, self.has_alpha, self.all_linear = self._read_header()

        # This is called 'index' in the reference code, but that would easy to confuse
        # with the '_ix' variable that tracks position
        if self.has_alpha:
            self._lookup = [RgbaPixel() for _ in range(64)]
        else:
            self._lookup = [RgbPixel() for _ in range(64)]
        self._pixels = []
        self._decode()

        # TODO: Reformat as RGB(A) array

    def _decode(self):
        while self._ix < (self._len - 8):
            this_byte = self.qoi_data[self._ix]
            self._ix += 1
            # First, check for the two 8-bit headers
            if this_byte == b"0xFE":
                # 1111 1110, RGB pixel
                log.debug(f"Raw RGB at {self._ix}")
                r, g, b = self.qoi_data[self._ix : self._ix + 3]
                self._pixels.append(RgbPixel(r, g, b))
                self._ix += 3

            elif this_byte == b"0xFF":
                # 1111 1111, RGBA pixel
                log.debug(f"Raw RGBA at {self._ix}")
                r, g, b, a = self.qoi_data[self._ix : self._ix + 4]
                self._pixels.append(RgbaPixel(r, g, b, a))
                self._ix += 4

            # Now on to the four two-bit tags
            elif (this_byte & QOI_MASK_2) == QOI_OP_INDEX:
                # Simple lookup
                log.debug(f"Index at {self._ix}")
                index = this_byte
                self._pixels.append(self._lookup[index])

            elif (this_byte & QOI_MASK_2) == QOI_OP_DIFF:
                # Each of this pixel's R, G, B values differs from the previous pixels'
                # by no more than [-2, 1]. Offsets are biased 2 (e.g. -2 = b00, 1 = b11)
                log.debug(f"OP_DIFF at {self._ix}")
                px = copy(self._pixels[-1])
                px.r += ((this_byte >> 4) & int("03", 16)) - 2
                px.g += int((this_byte >> 2) & int("03", 16)) - 2
                px.b += int(this_byte & int("03", 16)) - 2
                self._pixels.append(px)

            elif (this_byte & QOI_MASK_2) == QOI_OP_LUMA:
                # A more complex, two-byte transformation; see _qoi_op_luma()
                log.debug(f"OP_LUMA at {self._ix}")
                px = copy(self._pixels[-1])
                next_byte = self.qoi_data[self._ix]
                self._ix += 1
                d_r, d_g, d_b = self._qoi_op_luma(this_byte, next_byte)
                px.r += d_r
                px.g += d_g
                px.b += d_b
                self._pixels.append(px)

            elif (this_byte & QOI_MASK_2) == QOI_OP_RUN:
                log.debug(f"OP_RUN at {self._ix}")
                px = copy(self._pixels[-1])
                run_len = int(this_byte & ~QOI_MASK_2)
                self._pixels.extend((px for _ in range(run_len)))

            # TODO: If/when implementing streaming, need to check for closing bytes run

        # "The byte stream's end is marked with 7 0x00 bytes followed by a single 0x01
        # byte"
        remaining_data = self.qoi_data[self._ix :]
        assert (
            remaining_data == b"\x00" * 7 + b"\x01"
        ), f"Expected 0x0000000000000001, got {remaining_data.tohex()}"

    def __repr__(self):
        resolution = f"{self.width}x{self.height}"
        channel_str = "RGBA" if self.has_alpha else "RGB"
        colorspace_str = (
            "all channels linear" if self.all_linear else "sRGB with linear alpha"
        )
        return f"{resolution} {channel_str}, {colorspace_str}, {self._len} bytes packed"

    def _read_header(self):
        header_bytes = self.qoi_data[:14]
        width, height, has_alpha, all_linear = self.decode_header(
            header_bytes, validate=True
        )
        self._ix = 14
        return width, height, has_alpha, all_linear

    @staticmethod
    def _qoi_op_luma(first_byte, second_byte) -> Tuple[int, int, int]:
        """A two byte transform allowing for a larger shift from the previous pixel.

        Transformation description copied from specification:

        .- QOI_OP_LUMA -------------------------------------.
        |         Byte[0]         |         Byte[1]         |
        |  7  6  5  4  3  2  1  0 |  7  6  5  4  3  2  1  0 |
        |-------+-----------------+-------------+-----------|
        |  1  0 |  green diff     |   dr - dg   |  db - dg  |
        `---------------------------------------------------`
        2-bit tag b10
        6-bit green channel difference from the previous pixel -32..31
        4-bit   red channel difference minus green channel difference -8..7
        4-bit  blue channel difference minus green channel difference -8..7
        The green channel is used to indicate the general direction of change and is
        encoded in 6 bits. The red and blue channels (dr and db) base their diffs off
        of the green channel difference and are encoded in 4 bits. I.e.:
            dr_dg = (cur_px.r - prev_px.r) - (cur_px.g - prev_px.g)
            db_dg = (cur_px.b - prev_px.b) - (cur_px.g - prev_px.g)
        The difference to the current channel values are using a wraparound operation,
        so "10 - 13" will result in 253, while "250 + 7" will result in 1.
        Values are stored as unsigned integers with a bias of 32 for the green channel
        and a bias of 8 for the red and blue channel.
        The alpha value remains unchanged from the previous pixel.

        """
        d_g = int(first_byte & ~QOI_MASK_2) - 32
        dr_dg = ((second_byte & int("F0", 16)) >> 4) - 8
        db_dg = (second_byte & int("0F", 16)) - 8
        d_r = (d_g + dr_dg) & int("FF", 16)
        d_b = (d_g + db_dg) & int("FF", 16)
        return d_r, d_g, d_b

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
