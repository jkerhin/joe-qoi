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


class SignedChar(int):
    """Single-byte signed integer, [-128, 127]

    Integers in Python are immutable, so we must use the '__new__' method, not the
    '__init__' method to create a class instance.

    NB: Only addition and subtraction are needed in QOI encode/decode, so no other
    integer operations (e.g. multiply, bitwise operations, etc.) have been implemented.
    Since SignedChar subclasses 'int', these operations will work as expected, but the
    result will be cast to 'int' rather than 'SignedChar'.
    """

    def __new__(cls, value):
        mod_val = cls._wrap_around(value)
        return super(cls, cls).__new__(cls, mod_val)

    def __add__(self, other):
        res = super(SignedChar, self).__add__(other)
        res_mod = self._wrap_around(res)
        return self.__class__(res_mod)

    def __sub__(self, other):
        res = super(SignedChar, self).__sub__(other)
        res_mod = self._wrap_around(res)
        return self.__class__(res_mod)

    @staticmethod
    def _wrap_around(value):
        """Wrap around to keep range [-128, 127]"""
        if value > 127:
            return value - 256
        elif value < -128:
            return value + 256
        return value
