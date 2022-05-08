# joe-qoi

<!-- todo![![pypi](https://img.shields.io/pypi/v/joe-qoi.svg)](https://pypi.org/project/joe-qoi/) -->
<!-- [![Changelog](https://img.shields.io/github/v/release/jkerhin/joe-qoi?include_prereleases&label=changelog)](https://github.com/jkerhin/joe-qoi/releases) -->
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/jkerhin/joe-qoi/blob/main/LICENSE)

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

TODO: Usage instructions go here.

## Development

To contribute to this library, first checkout the code. Then create a new virtual environment:

    cd joe-qoi
    python -m venv venv
    source venv/bin/activate

Now install the dependencies and test dependencies:

    pip install -e '.[test]'

To run the tests:

    pytest
