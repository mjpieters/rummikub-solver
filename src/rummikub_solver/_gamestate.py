# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np

from ._types import Tile


class GameState:
    """State of a single game for one player.

    Tracks the tiles placed on the table and the rack, and if the player
    has managed to place the initial set of tiles from their rack.

    This is normally created by calling
    [`RuleSet.new_game()`][rummikub_solver.RuleSet.new_game].

    """

    _initial: bool  # initial state, False if the player has placed opening tiles

    _tile_map: Sequence[Tile]  # mapping from int to Tile objects
    _rack: Counter[Tile]  # tiles on the rack
    _table: Counter[Tile]  # tiles on the table

    # arrays maintained from the above counters for the solver
    # These use signed integers to simplify overflow handling when removing
    # tiles.
    _rack_array: np.typing.NDArray[np.int8]  # array with per-tile counts on the rack
    _table_array: np.typing.NDArray[np.int8]  # array with per-tile counts on the table

    def __init__(
        self,
        tile_map: Sequence[Tile],
        table: Iterable[Tile | int] | None = None,
        rack: Iterable[Tile | int] | None = None,
        initial: bool = True,
    ) -> None:
        self._tile_map = tile_map
        self.reset()
        if table:
            self.add_table(*table)
        if rack:
            self.add_rack(*rack)
        if not initial:
            self.initial = False

    @property
    def initial(self) -> bool:
        """Does this player still have to make their opening move."""
        return self._initial

    @initial.setter
    def initial(self, value: bool) -> None:
        self._initial = value

    @property
    def rack(self) -> Counter[Tile]:
        """The unique tiles on this rack, with their counts."""
        return self._rack

    @property
    def sorted_rack(self) -> list[Tile]:
        """The rack tiles as a sorted list."""
        return sorted(self._rack.elements())

    @property
    def table(self) -> Counter[Tile]:
        """The unique tiles on the table, with their counts."""
        return self._table

    @property
    def sorted_table(self) -> list[Tile]:
        """The table tiles as a sorted list."""
        return sorted(self._table.elements())

    # Solver-specific properties
    @property
    def rack_array(self) -> np.typing.NDArray[np.int8]:
        return self._rack_array

    @property
    def table_array(self) -> np.typing.NDArray[np.int8]:
        return self._table_array

    def reset(self) -> None:
        """Remove all tiles from the rack and table, and set the initial flag."""
        self._table, self._rack, self._initial = Counter(), Counter(), True
        self._table_array = np.zeros(len(self._tile_map) - 1, dtype=np.int8)
        self._rack_array = np.zeros(len(self._tile_map) - 1, dtype=np.int8)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<{type(self).__name__}([... {len(self._tile_map) - 1} tiles ...], "
            f"table={tuple(self.sorted_table)} rack={tuple(self.sorted_rack)}, "
            f"initial={self.initial})>"
        )

    def with_move(self, *tiles: Tile | int) -> GameState:
        """Create new state with specific tiles moved from rack to table.

        The tiles are verified to be on the rack and are moved to the table.
        This doesn't mutate this state, and instead creates a new state with
        the new tile locations.

        The new state will have the [`initial`
        flag][rummikub_solver.GameState.initial] cleared.

        Args:
            tiles: The tiles to remove from the rack and add to the table.

        Returns:
            The new state with the tiles moved.

        """
        tmap = self._tile_map
        moved = Counter(tmap[t] for t in tiles)
        if moved - self._rack:
            raise ValueError("Move includes tiles not on the rack")
        table = (self._table + moved).elements()
        rack = (self._rack - moved).elements()
        return type(self)(self._tile_map, table, rack, initial=False)

    def with_table(self, *tiles: Tile) -> GameState:
        """Create a new state with all table tiles replaced.

        This makes it simpler to pass the set of tiles on the table from player
        to player in a multi-player setup.

        Args:
            tiles: the tiles to add to the table.

        Returns:
            The new state with the additional tiles on the table.

        """
        return type(self)(
            self._tile_map, tiles, self.rack.elements(), initial=self.initial
        )

    def table_only(self) -> GameState:
        """Create new state with just the table tiles.

        Returns:
            The new game state with the rack empty.

        """
        return type(self)(self._tile_map, self.table.elements(), initial=self.initial)

    def add_rack(self, *tiles: Tile | int) -> None:
        """Add tiles to the rack.

        Tiles added are not validated against a ruleset.

        Args:
            tiles: The tiles to add to the rack.

        """
        if not tiles:
            return
        tmap = self._tile_map
        self._rack += Counter(tmap[t] for t in tiles)
        np.add.at(self._rack_array, np.array(tiles) - 1, 1)

    def remove_rack(self, *tiles: Tile | int) -> None:
        """Remove tiles from the rack.

        If any of the tiles passed in were not on the rack to begin with, they
        are ignored.

        Args:
            tiles: The tiles to remove from the rack.

        """
        if not tiles:
            return
        tmap = self._tile_map
        self._rack -= Counter(tmap[t] for t in tiles)
        rack = self._rack_array
        np.subtract.at(rack, np.array(tiles) - 1, 1)
        rack[rack < 0] = 0  # in case we removed tiles not on the rack

    def add_table(self, *tiles: Tile | int) -> None:
        """Add tiles to the table.

        Tiles added are not validated against a ruleset.

        Args:
            tiles: The tiles to remove from the rack.

        """
        if not tiles:
            return
        tmap = self._tile_map
        self._table += Counter(tmap[t] for t in tiles)
        np.add.at(self._table_array, np.array(tiles) - 1, 1)

    def remove_table(self, *tiles: Tile | int) -> None:
        """Remove tiles from the table.

        If any of the tiles passed in were not on the table to begin with, they
        are ignored.

        Args:
            tiles: The tiles to remove from the table.

        """
        if not tiles:
            return
        tmap = self._tile_map
        self._table -= Counter(tmap[t] for t in tiles)
        table = self._table_array
        np.subtract.at(table, np.array(tiles) - 1, 1)
        table[table < 0] = 0  # in case we removed tiles not on the table

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, GameState):  # pragma: no cover
            return NotImplemented
        return (self._initial, self._rack, self._table) == (
            other._initial,
            other._rack,
            other._table,
        )
