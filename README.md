# joe-qoi

<!-- TODO [![pypi](https://img.shields.io/pypi/v/joe-qoi.svg)](https://pypi.org/project/joe-qoi/) -->
[![Changelog](https://img.shields.io/github/v/release/jkerhin/joe-qoi?include_prereleases&label=changelog)](https://github.com/jkerhin/joe-qoi/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/jkerhin/joe-qoi/blob/main/LICENSE)

Pure Python implementation of QOI image format

## Installation

Install this library using `pip`:

    pip install joe-qoi

## Background

After watching [the Reducible video](https://www.youtube.com/watch?v=EFUYNoFRHQI) on PNG compression
that also discussed the QOI format, I wanted to take a stab at implementing QOI myself.

A quick peek at PyPi shows that there's already [an existing QOI package](https://pypi.org/project/qoi/)
that I'm sure will be immeasurably more performant than mine.

Since I want this to be a learning exercise, I'm going to implement it myself first without
referencing the Python QOI package, and then later take a look and see how our approaches
differ.

## Usage

The QOI format is _heavily_ optimized for low-level bitwise operations. Python, on the
other hand, is _not_ optimized for these kind of operations. As a result, this library
is _vastly_ less perforamant than the `c` reference code. E.g. decoding `dice.qoi` takes
3 **seconds** on my machine (over 45 seconds with DEBUG logging enabled).

The two classes of interest are the `QoiDecoder` class, which reads a QOI byte stream
and populates a list of `RgbaPixel`s, and `QoiEncoder` which takes image metadata and a
list of `RgbaPixel`s, and generates a QOI byte stream.

### Benchmarks

On an Intel i7-3770K, running Python 3.8.10 on Ubuntu 20.04 inside of WSL

```
$ python benchmark.py
        decode ms   encode ms   decode mpps   encode mpps   size kb    rate
joe-qoi:   3227.2      1802.5           0.1           0.3       507   27.1%     dice
joe-qoi:   5896.9      7262.7           0.1           0.1       637   55.3%     kodim10
joe-qoi:   5346.7      7604.7           0.1           0.1       659   57.2%     kodim23
joe-qoi:    415.7       108.6           0.2           0.9        16    4.2%     qoi_logo
joe-qoi:    369.4       178.8           0.2           0.4        21    8.3%     testcard
joe-qoi:    337.4       207.8           0.2           0.3        23    9.2%     testcard_rgba
joe-qoi:  13943.6     16543.5           0.1           0.1      1485   51.3%     wikipedia_008
```

## Development

To contribute to this library, first checkout the code. Then create a new virtual environment:

    cd joe-qoi
    python -m venv .venv
    source .venv/bin/activate

Now install the dev dependencies and test dependencies:

    pip install -r requirements-dev.txt

Next, configure `pre-commit`. Note that this will likely take a minute or so to
get set up the first time, unless you're using `pre-commit` in other projects.

    pre-commit install
    pre-commit run -a

To run the tests:

    pytest test
