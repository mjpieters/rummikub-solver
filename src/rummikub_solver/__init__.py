# SPDX-License-Identifier: MIT
"""Rummikub solver library.

A library to find possible moves for a Rummikub player given the tiles on their rack and the table.
"""

from ._gamestate import GameState
from ._ruleset import RuleSet
from ._types import (
    Colour,
    Joker,
    MILPSolver,
    Number,
    ProposedSolution,
    SolverMode,
    TableArrangement,
    Tile,
)
from ._version import __author__, __project__, __version__

__all__ = [
    "Colour",
    "GameState",
    "Joker",
    "MILPSolver",
    "Number",
    "ProposedSolution",
    "RuleSet",
    "SolverMode",
    "TableArrangement",
    "Tile",
    "__author__",
    "__project__",
    "__version__",
]
