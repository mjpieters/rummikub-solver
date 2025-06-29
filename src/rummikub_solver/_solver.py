# SPDX-License-Identifier: MIT
from __future__ import annotations

import logging
from itertools import chain
from typing import TYPE_CHECKING

import cvxpy as cp
import numpy as np

from ._gamestate import GameState
from ._types import DEFAULT_MILP_BACKENDS, MILPSolver, SolverMode, SolverSolution

if TYPE_CHECKING:
    from ._ruleset import RuleSet

_logger = logging.getLogger(__name__)


class RummikubSolver:
    """Solvers for finding possible tile placements in Rummikub games.

    Builds on the approach described by D. Den Hertog, P. B. Hulshof,
    Solving Rummikub Problems by Integer Linear Programming, The Computer
    Journal, Volume 49, Issue 6, November 2006, Pages 665-669,
    https://doi.org/10.1093/comjnl/bxl033

    Adapted to work with different Rummikub rulesets, including having
    a different number of possible jokers from repeated number tiles within
    the same colour, as well as much better initial tile placement and
    joker handling in general.

    Creates cvxpy solvers *once* and use parameters to improve efficiency.

    """

    def __init__(self, ruleset: RuleSet, backend: MILPSolver | None = None) -> None:
        if backend is None:
            supported = MILPSolver.supported()
            backend = next(d for d in DEFAULT_MILP_BACKENDS if d in supported)
        self.backend = backend

        # set membership matrix; how many copies of a given tile are present in
        # a given set. Each column is a set, each row a tile
        slen = len(ruleset.sets)
        smatrix = np.zeros((ruleset.tile_count, slen), dtype=np.uint8)
        np.add.at(
            smatrix,
            (
                np.fromiter(chain.from_iterable(ruleset.sets), np.uint8) - 1,
                np.repeat(
                    np.arange(slen), np.fromiter(map(len, ruleset.sets), np.uint16)
                ),
            ),
            1,
        )

        # Input parameters: counts for each tile on the table and on the rack
        table = self.table = cp.Parameter(ruleset.tile_count, "table", integer=True)
        rack = self.rack = cp.Parameter(ruleset.tile_count, "rack", integer=True)

        # Output variables: counts per resulting set, and counts per
        # tile taken from the rack to be added to the table.
        sets = self.sets = cp.Variable(len(ruleset.sets), "sets", integer=True)
        tiles = self.tiles = cp.Variable(ruleset.tile_count, "tiles", integer=True)

        # Constraints for the optimisation problem
        numbertiles = tiles
        joker_constraints = []
        if ruleset.jokers:
            numbertiles, jokers = tiles[:-1], tiles[-1]
            joker_constraints = [
                # You can place multiple jokers from your rack, but there are
                # never more than *ruleset.jokers* of them.
                jokers >= 0,
                jokers <= ruleset.jokers,
            ]

        constraints: list[cp.Constraint] = [
            # Both the table and the rack are non-negative
            table >= 0,
            rack >= 0,
            # placed sets can only be taken from selected rack tiles and what
            # was already placed on the table.
            smatrix @ sets == table + tiles,
            # the selected tiles must all come from your rack
            tiles <= rack,
            # A given set could appear multiple times, but never more than
            # *repeats* times.
            sets >= 0,
            sets <= ruleset.repeats,
            # You can place multiple tiles with the same colour and number
            # but there are never more than *ruleset.repeats* of them.
            numbertiles >= 0,
            numbertiles <= ruleset.repeats,
            # variable joker constraints for the current ruleset
            *joker_constraints,
        ]

        p: dict[SolverMode, cp.Problem] = {}
        # Problem solver maximising number of tiles placed
        p[SolverMode.TILE_COUNT] = cp.Problem(cp.Maximize(cp.sum(tiles)), constraints)  # type: ignore[reportUnknownMemberType]

        # Problem solver maximising the total value of tiles placed
        tilevalue = np.tile(
            np.arange(ruleset.numbers, dtype=np.uint16) + 1, ruleset.colours
        )
        if ruleset.jokers:
            tilevalue = np.append(tilevalue, 0)
        p[SolverMode.TOTAL_VALUE] = cp.Problem(
            cp.Maximize(cp.sum(tiles[:, np.newaxis] @ tilevalue[np.newaxis, :])),  # type: ignore[reportUnknownMemberType]
            constraints,
        )

        # Problem solver used for the opening move ("initial meld").
        # Initial meld scoring is based entirely on the sets formed, and must
        # be equal to or higher than the minimal score. Maximize the tile count
        # _without jokers_.
        setvalue = np.array(ruleset.set_values, dtype=np.uint16)
        initial_constraints = [
            *constraints,
            sets @ setvalue >= ruleset.min_initial_value,
        ]
        p[SolverMode.INITIAL] = cp.Problem(
            cp.Maximize(cp.sum(numbertiles)),  # type: ignore[reportUnknownMemberType]
            initial_constraints,
        )

        self._problems = p

    def __call__(self, mode: SolverMode, state: GameState) -> SolverSolution:
        """Find a solution for the given game state.

        Uses the appropriate objective for the given solver mode, and takes
        the rack tile count and table tile count from state.

        """
        # set parameters
        self.rack.value = state.rack_array
        if mode is SolverMode.INITIAL:
            # can't use tiles on the table, set all counts to 0
            self.table.value = np.zeros_like(state.table_array)
        else:
            self.table.value = state.table_array

        prob = self._problems[mode]
        try:
            value = prob.solve(solver=self.backend)  # type: ignore[reportUnknownMemberType]
        except cp.SolverError:  # pragma: no cover
            # solver threw a hissyfit, treat as 'no solution'
            _logger.debug(
                f"{self.backend} threw an error while trying to solve, treating as no solution"
            )
            value = float("-inf")
        if TYPE_CHECKING:
            assert isinstance(value, float)
        if np.isinf(value):
            # no solution for the problem (e.g. no combination of tiles on
            # the rack leads to a valid set or has enough points when opening)
            return SolverSolution((), ())

        # convert index counts to repeated indices, as Python scalars
        # similar to what Counts.elements() produces.
        if TYPE_CHECKING:
            assert self.tiles.value is not None
        tiles = np.rint(self.tiles.value).astype(int)
        (tidx,) = tiles.nonzero()
        # add 1 to the indices to get tile numbers
        selected_tiles = np.repeat(tidx + 1, tiles[tidx]).tolist()

        if TYPE_CHECKING:
            assert self.sets.value is not None
        sets = np.rint(self.sets.value).astype(int)
        (sidx,) = sets.nonzero()
        selected_sets = np.repeat(sidx, sets[sidx]).tolist()

        return SolverSolution(selected_tiles, selected_sets)
