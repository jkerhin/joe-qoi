"""Benchmark joe-qoi against the qoi_test_images

Pulling the format string form the reference C code's benchmark file:
    https://github.com/phoboslab/qoi/blob/master/qoibench.c

If you don't have qoi_test_images pulled locally, there are instructions in
test/conftest.py

Note that I'm not conducting multiple runs and getting an average - the throughput of
this library is so low that I don't want to wait on multiple runs.
"""
import time
from dataclasses import dataclass
from pathlib import Path

from joe_qoi import codecs

TEST_FILE_ROOT = Path(__file__).parent / "qoi_test_images"
TEST_FILE_BASENAMES = [
    "dice",
    "kodim10",
    "kodim23",
    "qoi_logo",
    "testcard",
    "testcard_rgba",
    "wikipedia_008",
]


@dataclass
class Benchmark:
    file_name: str
    decode_ns: int
    encode_ns: int
    num_pix: int
    size_raw: int
    size_encoded: int

    @property
    def decode_ms(self) -> float:
        return self.decode_ns / 1e6

    @property
    def encode_ms(self) -> float:
        return self.encode_ns / 1e6

    @property
    def decode_mpps(self) -> float:
        return self.num_pix / (self.decode_ns / 1e3)

    @property
    def encode_mpps(self) -> float:
        return self.num_pix / (self.encode_ns / 1e3)

    @property
    def size_kb(self) -> int:
        return int(self.size_encoded / 1024)

    @property
    def ratio(self) -> float:
        return self.size_encoded / float(self.size_raw)


def benchmark_decode(in_bytes: bytes) -> codecs.QoiDecoder:
    return codecs.QoiDecoder(in_bytes)


def benchmark_encode(decoder: codecs.QoiDecoder):
    return codecs.QoiEncoder(
        rgba_pixels=decoder.pixels,
        width=decoder.width,
        height=decoder.height,
        has_alpha=decoder.has_alpha,
        all_linear=decoder.all_linear,
    )


def run_benchmark(base_name) -> Benchmark:
    source_bytes = (TEST_FILE_ROOT / f"{base_name}.qoi").read_bytes()

    # Benchmark decode
    t0 = time.perf_counter_ns()
    qd = benchmark_decode(source_bytes)
    t1 = time.perf_counter_ns()
    decode_ns = t1 - t0
    size_raw = qd._num_pixels * (4 if qd.has_alpha else 3)

    # Benchmark encode
    t0 = time.perf_counter_ns()
    qe = benchmark_encode(qd)
    t1 = time.perf_counter_ns()
    encode_ns = t1 - t0
    size_encoded = len(bytes(qe))

    return Benchmark(
        file_name=base_name,
        decode_ns=decode_ns,
        encode_ns=encode_ns,
        num_pix=qd._num_pixels,
        size_raw=size_raw,
        size_encoded=size_encoded,
    )


def main():
    h = "        decode ms   encode ms   decode mpps   encode mpps   size kb    rate"
    print(h)
    for base_name in TEST_FILE_BASENAMES:
        bm = run_benchmark(base_name)
        out_str = (
            f"joe-qoi: {bm.decode_ms:8.1f}    {bm.encode_ms:8.1f}      "
            f"{bm.decode_mpps:8.1f}      {bm.encode_mpps:8.1f}  {bm.size_kb:>8d}   "
            f"{bm.ratio * 100:4.1f}%\t{base_name}"
        )
        print(out_str)


if __name__ == "__main__":
    main()
