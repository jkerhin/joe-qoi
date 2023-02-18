"""Run tests with multiple versions of python, locally

NOTE: This requires the use of the `nox` package, which is not defined in the either
requirements.txt or requirements-dev.txt. Since `nox` creates and manages its own
virtual environments, it makes more sense for nox to be installed system-wide than to
install it project-specific.

pipx works extremely well for managing standalone python tools. Installing nox with pipx
is as simple as:
    pipx install nox

Once nox is installed, running the bare `nox` command from the project root will prompt
nox to run the test suite locally for all availible Python interpreters 3.7 - 3.11
"""
import nox


@nox.session(python=["3.7", "3.8", "3.9", "3.10", "3.11"])
def test(session):
    """Setup interpreter-specific virtual environment, and run test suite with pytest

    To run the full (very slow) test suite, invoke nox like so:
        nox -- --run-slow
    """
    session.install(".[test]")
    session.run("pytest", *session.posargs)
