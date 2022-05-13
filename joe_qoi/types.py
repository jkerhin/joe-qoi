import struct
from dataclasses import dataclass


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
