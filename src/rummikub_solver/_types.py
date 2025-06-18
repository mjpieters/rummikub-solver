# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections.abc import Sequence
from enum import Enum, auto
from typing import NamedTuple, Self


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
