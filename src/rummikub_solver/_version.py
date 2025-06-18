# SPDX-License-Identifier: MIT
from importlib.metadata import PackageNotFoundError, metadata, version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    assert __package__ is not None

try:
    __version__ = version(__package__)
    _info = metadata(__package__)
    __project__, __author__ = _info["name"], _info["author-email"]
    del _info
except PackageNotFoundError:  # pragma: no cover
    # package is not installed
    __version__ = "<unknown>"
    __project__ = __name__
    __author__ = "<unknown>"
