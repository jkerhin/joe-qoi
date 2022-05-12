"""Encoding and Decoding operations for QOI format"""
import logging
import struct
from copy import copy
from dataclasses import dataclass
from typing import Iterable, List, Tuple, Union

log = logging.getLogger(__name__)
# fmt: off
QOI_OP_INDEX = int("00", 16)  # b00xxxxxxxx
QOI_OP_DIFF  = int("40", 16)  # b01xxxxxxxx
QOI_OP_LUMA  = int("80", 16)  # b10xxxxxxxx
QOI_OP_RUN   = int("C0", 16)  # b11xxxxxxxx
QOI_OP_RGB   = int("FE", 16)  # b1111111110
QOI_OP_RGBA  = int("FF", 16)  # b1111111111
QOI_MASK_2   = int("C0", 16)  # b11xxxxxxxx
# fmt: on


@dataclass
class RgbaPixel:
    r: int = 0
    g: int = 0
    b: int = 0
    a: int = 0

    @property
    def packed_rgb(self) -> bytes:
        return struct.pack(">BBB", self.r, self.g, self.b)

    @property
    def packed_rgba(self) -> bytes:
        return struct.pack(">BBBB", self.r, self.g, self.b, self.a)


def qoi_color_hash(r: int, g: int, b: int, a: int) -> int:
    """Hashing function used to populate and index into the 64-pixel lookup table"""
    return (r * 3 + g * 5 + b * 7 + a * 11) % 64


# TODO: Find a better place for this...
def wrap_around(val: int) -> int:
    """Implement 'signed character' wraparound logic"""
    if val > 127:
        return val - 256
    elif val < -128:
        return val + 256
    return val


class QoiEncoder:
    def __init__(
        self,
        rgba_pixels: List[RgbaPixel],
        width: int,
        height: int,
        has_alpha: bool,
        all_linear: bool,
    ):
        self.rgba_pixels = rgba_pixels
        self.width = width
        self.height = height
        self.has_alpha = has_alpha
        self.all_linear = all_linear

        # This is called 'index' in the reference code, but that would easy to confuse
        # with the '_ix' variable that tracks position
        self._lookup = [RgbaPixel() for _ in range(64)]
        self.packed_bytes: bytearray = bytearray()

        self._encode()

    def _encode(self):
        raise NotImplementedError

    def __repr__(self):
        resolution = f"{self.width}x{self.height}"
        channel_str = "RGBA" if self.has_alpha else "RGB"
        colorspace_str = (
            "all channels linear" if self.all_linear else "sRGB with linear alpha"
        )
        n_bytes = len(self.rgba_pixels) * (4 if self.has_alpha else 3)
        return f"{resolution} {channel_str}, {colorspace_str}, {n_bytes} bytes to pack"

    @staticmethod
    def pack_rgb(px: RgbaPixel) -> bytes:
        """Pack RGB pixel with QOI_OP_RGB tag and r, g, b pixel values"""
        return bytes((QOI_OP_RGB, px.r, px.g, px.b))

    @staticmethod
    def pack_rgba(px: RgbaPixel) -> bytes:
        """Pack RGBA pixel with QOI_OP_RGB tag and r, g, b, a pixel values"""
        return bytes((QOI_OP_RGBA, px.r, px.g, px.b, px.a))

    @staticmethod
    def pack_index(index: int) -> bytes:
        """Index into the "recently seen pixels" lookup table

        .- QOI_OP_INDEX ----------.
        |         Byte[0]         |
        |  7  6  5  4  3  2  1  0 |
        |-------+-----------------|
        |  0  0 |     index       |
        `-------------------------`
        2-bit tag b00
        6-bit index into the color index array: 0..63

        A valid encoder must not issue 2 or more consecutive QOI_OP_INDEX chunks to the
        same index. QOI_OP_RUN should be used instead.

        """
        if not 0 < index < 63:
            raise ValueError("QOI_OP_INDEX allowed range is [0, 63]")
        return bytes([index])

    @staticmethod
    def pack_diff(prev_px: RgbaPixel, this_px: RgbaPixel) -> bytes:
        """Store RGB deltas between two very closely spaced pixels, and QOI_OP_DIFF tag

        .- QOI_OP_DIFF -----------.
        |         Byte[0]         |
        |  7  6  5  4  3  2  1  0 |
        |-------+-----+-----+-----|
        |  0  1 |  dr |  dg |  db |
        `-------------------------`
        2-bit tag b01
        2-bit   red channel difference from the previous pixel between -2..1
        2-bit green channel difference from the previous pixel between -2..1
        2-bit  blue channel difference from the previous pixel between -2..1

        The difference to the current channel values are using a wraparound operation,
        so "1 - 2" will result in 255, while "255 + 1" will result in 0.

        Values are stored as unsigned integers with a bias of 2. E.g. -2 is stored as
        0 (b00). 1 is stored as 3 (b11).

        The alpha value remains unchanged from the previous pixel.

        """
        dr = wrap_around(this_px.r - prev_px.r)
        dg = wrap_around(this_px.g - prev_px.g)
        db = wrap_around(this_px.b - prev_px.b)

        if not all(-2 <= d <= 1 for d in (dr, dg, db)):
            raise ValueError("QOI_OP_DIFF all deltas must be in range [-2, 1]")

        out_byte_as_int = 0  # 0x00
        out_byte_as_int |= QOI_OP_DIFF
        out_byte_as_int |= (dr + 2) << 4
        out_byte_as_int |= (dg + 2) << 2
        out_byte_as_int |= db + 2

        return bytes([out_byte_as_int])

    @staticmethod
    def pack_luma(prev_px: RgbaPixel, this_px: RgbaPixel) -> bytes:
        """Store RGB deltas between two closely spaced pixels, and QOI_OP_LUMA tag

        Allows for a large pixel differnece than QOI_OP_DIFF, at the cost of an
        additional byte.

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
        dr = wrap_around(this_px.r - prev_px.r)
        dg = wrap_around(this_px.g - prev_px.g)
        db = wrap_around(this_px.b - prev_px.b)

        if not -32 <= dg <= 31:
            raise ValueError("QOI_OP_LUMA green delta must be in range [-32, 31]")

        dr_dg = wrap_around(dr - dg)
        db_dg = wrap_around(db - dg)

        if not all(-8 <= d <= 7 for d in (dr_dg, db_dg)):
            raise ValueError(
                "QOI_OP_LUMA red, blue offsets from green must be in range [-8, 7]"
            )

        out_byte_1_as_int = 0  # 0x00
        out_byte_1_as_int |= QOI_OP_LUMA
        out_byte_1_as_int |= dg + 32

        out_byte_2_as_int = (dr_dg + 8) << 4
        out_byte_2_as_int |= db_dg + 8

        return bytes([out_byte_1_as_int, out_byte_2_as_int])

    @staticmethod
    def pack_run(count: int) -> bytes:
        """Indicate that the preceding pixel should be repeated 'count' times

        .- QOI_OP_RUN ------------.
        |         Byte[0]         |
        |  7  6  5  4  3  2  1  0 |
        |-------+-----------------|
        |  1  1 |       run       |
        `-------------------------`
        2-bit tag b11
        6-bit run-length repeating the previous pixel: 1..62

        The run-length is stored with a bias of -1. Note that the run-lengths 63 and 64
        (b111110 and b111111) are illegal as they are occupied by the QOI_OP_RGB and
        QOI_OP_RGBA tags.

        """
        if not 1 < count < 62:
            raise ValueError("QOI_OP_RUN allowed range is [1, 62]")

        out_byte_as_int = 0  # 0x00
        out_byte_as_int |= QOI_OP_RUN
        out_byte_as_int |= count - 1

        return bytes([out_byte_as_int])

    @staticmethod
    def encode_header(
        width: int, height: int, has_alpha: bool, all_linear: bool
    ) -> bytes:
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
        header = bytearray(14)
        header[:4] = "qoif".encode("ASCII")  # "magic" bytes

        struct.pack_into(">II", header, 4, width, height)

        channels = 4 if has_alpha else 3
        colorspace = 1 if all_linear else 0
        struct.pack_into(">BB", header, 12, channels, colorspace)

        return bytes(header)

    @classmethod
    def from_bytes(
        cls,
        bytes_in: Union[bytearray, Iterable[bytes]],
        width: int,
        height: int,
        has_alpha: bool,
        all_linear: bool,
    ):
        """Create a QoiEncoder from raw bytes and metadata"""
        bytes_per_pix = 4 if has_alpha else 3
        rgba_pixels: List[RgbaPixel] = []
        for offset in range(0, len(bytes_in), bytes_per_pix):
            px = RgbaPixel(*bytes_in[offset : offset + bytes_per_pix])
            if not has_alpha:
                px.a = 255
            rgba_pixels.append(px)
        return cls(rgba_pixels, width, height, has_alpha, all_linear)

    @classmethod
    def from_ppm(cls, file_name: str):
        """Create a QoiEncoder from a Netpbm file

        For simplicity's sake, this only suports handling binary RGB (P6) files. I'm
        sure it wouldn't be a huge lift to code up greyscale/BW decoder, but this is a
        QOI library not a Netpbm library.

        Read the file size from the PPM header, then pass the data to from_bytes(). PPM
        does not support alpha channel, so has_alpha=False

        """
        with open(file_name, "rb") as hdl:
            ppm = hdl.read()

        ppm_type, w_h, max_val, data = ppm.split(b"\n")
        ppm_type = ppm_type.decode("ASCII")
        max_val = max_val.decode("ASCII")

        if (ppm_type != "P6") or (max_val != "255"):
            raise IOError(
                f"Unsupported Netpbf file. Expected P6, 255 got {ppm_type}, {max_val}"
            )

        width, height = map(int, w_h.decode("ASCII").split())

        return cls.from_bytes(
            bytes_in=data, width=width, height=height, has_alpha=False, all_linear=True
        )


class QoiDecoder:
    def __init__(self, qoi_data: bytes):
        self.qoi_data = qoi_data
        self._ix = 0
        self._qoi_data_len = len(qoi_data)

        self.width, self.height, self.has_alpha, self.all_linear = self._read_header()
        self._num_pixels = self.width * self.height

        # This is called 'index' in the reference code, but that would easy to confuse
        # with the '_ix' variable that tracks position
        self._lookup = [RgbaPixel() for _ in range(64)]
        self.pixels: List[RgbaPixel] = []
        self._decode()
        if len(self.pixels) != self._num_pixels:
            raise IOError(
                f"Improper decode! Expected {self._num_pixels} got {len(self.pixels)}"
            )

        # TODO: Reformat as RGB(A) array

    def _decode(self):
        """Decode the qoi_data stream"""
        pixel_pos = 0
        px = RgbaPixel(r=0, g=0, b=0, a=255)
        while self._ix < (self._qoi_data_len - 8):
            this_byte = self.qoi_data[self._ix]
            self._ix += 1
            # First, check for the two 8-bit headers
            if this_byte == QOI_OP_RGB:
                # Full RGB pixel values
                log.debug(f"Raw RGB at {self._ix} - {pixel_pos}")
                r, g, b = self.qoi_data[self._ix : self._ix + 3]
                px.r = r
                px.g = g
                px.b = b
                self._ix += 3

            elif this_byte == QOI_OP_RGBA:
                # Full RGBA pixel values
                log.debug(f"Raw RGBA at {self._ix} - {pixel_pos}")
                r, g, b, a = self.qoi_data[self._ix : self._ix + 4]
                px.r = r
                px.g = g
                px.b = b
                px.a = a
                self._ix += 4

            # Now on to the four two-bit tags
            elif (this_byte & QOI_MASK_2) == QOI_OP_INDEX:
                # Simple lookup
                log.debug(f"Index op at {self._ix} - {pixel_pos}")
                index = this_byte
                px = self._lookup[index]
                log.debug(f"Index - {index} - {px}")

            elif (this_byte & QOI_MASK_2) == QOI_OP_DIFF:
                # Each of this pixel's R, G, B values differs from the previous pixels'
                # by no more than [-2, 1]. Offsets are biased 2 (e.g. -2 = b00, 1 = b11)
                log.debug(f"OP_DIFF at {self._ix} - {pixel_pos}")
                px.r += ((this_byte >> 4) & int("03", 16)) - 2
                px.g += int((this_byte >> 2) & int("03", 16)) - 2
                px.b += int(this_byte & int("03", 16)) - 2

            elif (this_byte & QOI_MASK_2) == QOI_OP_LUMA:
                # A more complex, two-byte transformation; see _qoi_op_luma()
                log.debug(f"OP_LUMA at {self._ix} - {pixel_pos}")
                next_byte = self.qoi_data[self._ix]
                self._ix += 1
                d_r, d_g, d_b = self._qoi_op_luma(this_byte, next_byte)
                px.r += d_r
                px.g += d_g
                px.b += d_b

            elif (this_byte & QOI_MASK_2) == QOI_OP_RUN:
                # A run of repeating pixels. Note a bias of 1 to allow runs of 1..62
                # pixels. Run lengths of 63 and 64 px are illegal as they are occupied
                # by the QOI_OP_RGB and QOI_OP_RGBA tags.
                log.debug(f"OP_RUN at {self._ix} - {pixel_pos}")
                run_len = int(this_byte & ~QOI_MASK_2)
                run_len += 1
                log.debug(f"Run of {run_len}")
                self.pixels.extend((copy(px) for _ in range(run_len)))
                pixel_pos = len(self.pixels)
                continue

            # TODO: If/when implementing streaming, need to check for closing bytes run

            # Force [0, 255] range
            px.r &= int("FF", 16)
            px.g &= int("FF", 16)
            px.b &= int("FF", 16)
            px.a &= int("FF", 16)

            hash_index = qoi_color_hash(px.r, px.g, px.b, px.a)
            self._lookup[hash_index] = copy(px)
            self.pixels.append(copy(px))
            pixel_pos = len(self.pixels)

            if len(self.pixels) > self._num_pixels:
                log.error(f"More pixels than expected! Bailing out at {self._ix}")
                return

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
        return f"{resolution} {channel_str}, {colorspace_str}, {self._qoi_data_len} bytes packed"

    def _read_header(self):
        header_bytes = self.qoi_data[:14]
        width, height, has_alpha, all_linear = self.decode_header(
            header_bytes, validate=True
        )
        self._ix = 14
        log.debug(f"Header: {width}x{height}, alpha: {has_alpha}, linear: {all_linear}")
        return width, height, has_alpha, all_linear

    def write_ppm(self, out_file: str):
        """Serialize pixel array to Netpbm format file

        The Netpbm format is trivial to serialize, and allows for visual inspection of
        the decoded stream.

        This function implements the Binary PPM format - full RGB but no alpha, binary
        encoding of the pixel values rather than ASCII

        ref: https://en.wikipedia.org/wiki/Netpbm
        """
        ppm_header = [
            "P6",  # Binary RGB PPM
            f"{self.width} {self.height}",
            "255",  # Maximum value for each color
        ]
        with open(out_file, "wb") as hdl:
            for line in ppm_header:
                hdl.write(f"{line}\n".encode("ASCII"))
            for px in self.pixels:
                hdl.write(px.packed_rgb)
        logging.info(f"Wrote PPM to {out_file}")

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
