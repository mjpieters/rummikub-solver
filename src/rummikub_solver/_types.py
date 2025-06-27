# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections.abc import Sequence
from enum import Enum, StrEnum, auto
from typing import NamedTuple, Self

from ._utils import enum_docstrings


class Colour(Enum):
    """Tile colours.

    These are assigned to tiles in the order they are defined in this enum.

    """

    BLACK = auto()
    BLUE = auto()
    ORANGE = auto()
    RED = auto()
    GREEN = auto()
    MAGENTA = auto()
    WHITE = auto()
    CYAN = auto()


class Tile(int):
    """Base class for tiles.

    The exact integer value of each tile is dependent on a given [`RuleSet`][rummikub_solver.RuleSet].
    """

    def __repr__(self) -> str:
        return "-"


class Joker(Tile):
    """A joker tile."""

    def __repr__(self) -> str:
        return f"<Joker ({int(self)})>"


class Number(Tile):
    """A number tile.

    The exact integer value of each number tile is dependent on a given
    [`RuleSet`][rummikub_solver.RuleSet], and tiles are best retrieved
    from the [`RuleSet.tiles` sequence][rummikub_solver.RuleSet.tiles].
    """

    def __new__(cls, tile: int, colour: Colour, value: int) -> Self:
        instance = super().__new__(cls, tile)
        instance.value = value
        instance.colour = colour
        return instance

    value: int
    """The numeric value"""
    colour: Colour
    """The tile colour"""

    def __repr__(self) -> str:
        col = self.colour.name.title()
        return f"<{col} {self.value} ({int(self)})>"

    def __getnewargs__(self) -> tuple[int, Colour, int]:  # type: ignore[reportIncompatibleMethodOverride]
        return (*super().__getnewargs__(), self.colour, self.value)


class SolverMode(Enum):
    INITIAL = "initial"
    """Initial placement mode, player can only use tiles from their own rack"""
    TILE_COUNT = "tiles"
    """Maximize the number of tiles placed"""
    TOTAL_VALUE = "value"
    """Maximize the total value of the tiles placed"""


class SolverSolution(NamedTuple):
    """Raw solver solution, containing tile values and set indices."""

    tiles: Sequence[int]
    # indices into the ruleset sets list
    set_indices: Sequence[int]


class ProposedSolution(NamedTuple):
    """Proposed next move to make for a given game state."""

    tiles: Sequence[Tile]
    """What tiles to move from the rack to the table"""
    sets: Sequence[tuple[Tile, ...]]
    """What sets to form with rack tiles combined with table tiles"""
    free_jokers: int = 0
    """Number of free jokers on the table.
    
    If this value is non-zero, the jokers where free to begin with and the
    solver was not able to find a better solution that utilised these jokers.

    One scenario this can happen is if a player can place all their tiles
    from the rack on to the table in an initial meld, including a joker that
    becomes free once combined with other tiles on the table. Since the
    player has already won this is not an issue.

    """


class TableArrangement(NamedTuple):
    """Possible arrangement for tiles on the table.

    Includes a count of how many jokers are redundant (can be used freely).

    """

    sets: Sequence[tuple[Tile, ...]]
    """Table sets
    
    This is one possible arrangement of the tiles present on the table.
    
    """
    free_jokers: int
    """Number of free jokers on the table"""


@enum_docstrings
class MILPSolver(StrEnum):
    """Mixed-integer Linear Programming solver to use."""

    # OSS solvers
    CBC = "CBC"
    """COIN-OR (EPL-2.0), <https://github.com/coin-or/CyLP>"""

    GLPK_MI = "GLPK_MI"
    """GNU Linear Programming Kit (GPL-3.0-only), <https://www.gnu.org/software/glpk/> (via [`cvxopt`](https://pypi.org/p/cvxopt))"""

    HIGHS = "HIGHS"
    """HiGHS (MIT), <https://highs.dev/> (via [`highspy`](https://pypi.org/p/highspy))"""

    SCIP = "SCIP"
    """SCIP (Apache-2.0), <https://scipopt.org/> (via [`pyscipopt`](https://pypi.org/p/pyscipopt))"""

    SCIPY = "SCIPY"
    """SciPy (BSD-3-Clause), <https://scipy.org/>, default solver (built on HiGHS)"""

    # Commercial solvers
    COPT = "COPT"
    """COPT (LicenseRef-Proprietary), <https://github.com/COPT-Public/COPT-Release>"""

    CPLEX = "CPLEX"
    """IBM CPLEX (LicenseRef-Proprietary), <https://www.ibm.com/docs/en/icos>"""

    GUROBI = "GUROBI"
    """Gurobi (LicenseRef-Proprietary), <https://www.gurobi.com/>"""

    MOSEK = "MOSEK"
    """Mosek (LicenseRef-Proprietary), <https://www.mosek.com/>"""

    XPRESS = "XPRESS"
    """Fico XPress, (LicenseRef-Proprietary), <https://www.fico.com/en/products/fico-xpress-optimization>"""

    @classmethod
    def supported(cls) -> set[Self]:
        """All currently available solver backends, based on what is installed.

        Returns:
            All the backends that are currently installed.

        """
        from cvxpy import installed_solvers

        installed: set[str] = set(installed_solvers())
        return {member for member in cls if member in installed}


# These are tried in order based on what is installed
DEFAULT_MILP_BACKENDS = (MILPSolver.HIGHS, MILPSolver.SCIPY)
