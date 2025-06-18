# SPDX-License-Identifier: MIT
"""MILPSolver fixture support.

This adds a --solver-backend command line switch with help information,
a test report header showing what was selected, and fixture generation
from the command-line switch or default.

"""

import pytest

from rummikub_solver import MILPSolver

OSS_BACKENDS = {
    backend
    for backend in MILPSolver
    if backend.__doc__ and "LicenseRef-Proprietary" not in backend.__doc__
}
SELECTED_BACKENDS = pytest.StashKey[list[MILPSolver]]()


__all__ = [
    "pytest_addoption",
    "pytest_generate_tests",
    "pytest_report_header",
    "pytest_sessionstart",
]


# Add a --solver-backend switch to pytest to allow picking arbitrary backends.
# The default is to parametrize on OSS backends.
def pytest_addoption(
    parser: pytest.Parser, pluginmanager: pytest.PytestPluginManager
) -> None:
    supported = MILPSolver.supported()
    options: list[str] = []
    if oss_installed := [
        str(backend) for backend in MILPSolver if backend in OSS_BACKENDS & supported
    ]:
        options.append(f"OSS backends (installed): {', '.join(oss_installed)}")
    if oss_not_installed := [
        str(backend) for backend in MILPSolver if backend in OSS_BACKENDS - supported
    ]:
        options.append(f"OSS backends (not installed): {', '.join(oss_not_installed)}")
    if prop_installed := [
        str(backend) for backend in MILPSolver if backend in supported - OSS_BACKENDS
    ]:
        options.append(f"Proprietary backends (installed): {', '.join(prop_installed)}")
    if prop_not_installed := [
        str(backend)
        for backend in MILPSolver
        if backend not in OSS_BACKENDS | supported
    ]:
        options.append(
            f"Proprietary backends (not installed): {', '.join(prop_not_installed)}"
        )

    backends = "\n".join(options)
    parser.addoption(
        "--solver-backend",
        action="append",
        default=[],
        choices=[str(backend) for backend in MILPSolver],
        help=(
            "list of solver backends (rummikub_solver.MILPSolver members) to "
            "test against. Defaults to all Open Source Software (OSS) backends. "
            "Any selected but not currently installed backends will be skipped.\n"
            f"{backends}"
        ),
    )


def pytest_sessionstart(session: pytest.Session) -> None:
    selected: list[str] = session.config.getoption("solver_backend")
    session.config.stash[SELECTED_BACKENDS] = [
        MILPSolver(name) for name in selected
    ] or [backend for backend in MILPSolver if backend in OSS_BACKENDS]


def pytest_report_header(config: pytest.Config) -> str:
    selected = config.stash[SELECTED_BACKENDS]
    return f"selected solver backends: {', '.join(selected)}"


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "solver_backend" in metafunc.fixturenames:
        installed = MILPSolver.supported()
        backends = metafunc.config.stash[SELECTED_BACKENDS]
        if all(backend not in installed for backend in backends):
            metafunc.definition.warn(
                pytest.PytestCollectionWarning(
                    f"None of the selected solver backends are installed: "
                    f"{', '.join(metafunc.config.getoption('solver_backend'))}."
                )
            )
        metafunc.parametrize(
            "solver_backend",
            [
                pytest.param(
                    backend,
                    marks=pytest.mark.skipif(
                        backend not in installed, reason=f"{backend} not installed"
                    ),
                )
                for backend in backends
            ],
        )
