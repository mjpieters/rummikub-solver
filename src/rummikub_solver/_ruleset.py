# SPDX-License-Identifier: MIT
from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Sequence, Sized
from functools import cached_property
from itertools import chain, combinations, islice, product, repeat
from typing import TYPE_CHECKING, Annotated, cast

from ._gamestate import GameState
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
from ._utils import validate_intervals

if TYPE_CHECKING:
    from annotated_types import Interval


_logger = logging.getLogger(__name__)


class RuleSet:
    """Manages all aspects of a specific set of Rummikub rules.

    The default settings reflect the rules for a standard (Sabra rules) Rummikub game.

    Note that you can't create rulesets where
    [`min_len`][rummikub_solver.RuleSet.min_len] is greater than
    [`numbers`][rummikub_solver.RuleSet.numbers] or
    [`colours`][rummikub_solver.RuleSet.colours], because then there are no
    legal sets possible. All numeric arguments are validated and will result in
    a [`ValueError`][ValueError] if they do not fall within their
    specified interval.

    """

    @validate_intervals
    def __init__(
        self,
        *,
        numbers: Annotated[int, Interval(ge=2, le=26)] = 13,
        repeats: Annotated[int, Interval(ge=1, le=4)] = 2,
        colours: Annotated[int, Interval(ge=2, le=8)] = 4,
        jokers: Annotated[int, Interval(ge=0, le=4)] = 2,
        min_len: Annotated[int, Interval(ge=2, le=6)] = 3,
        min_initial_value: Annotated[int, Interval(ge=1, le=50)] = 30,
        solver_backend: MILPSolver | None = None,
    ) -> None:
        if numbers <= colours and min_len > numbers:
            raise ValueError(
                f"min_len={min_len} must be smaller than or equal to numbers={numbers}"
            )
        elif min_len > colours:
            raise ValueError(
                f"min_len={min_len} must be smaller than or equal to colours={colours}"
            )

        self._numbers = numbers
        self._repeats = repeats
        self._colours = colours
        self._jokers = jokers
        self._min_len = min_len
        self._min_initial_value = min_initial_value

        self._tile_count = numbers * colours
        self._joker = None
        if jokers:
            self._tile_count += 1
            self._joker = Joker(self._tile_count)

        self._tiles = self._tile_map()
        self.backend = solver_backend

    def _tile_map(self) -> tuple[Tile, ...]:
        cols, nums = islice(Colour, self._colours), range(1, self._numbers + 1)
        tiles: list[Tile] = [
            Number(t, *cn) for t, cn in enumerate(product(cols, nums), 1)
        ]
        return (Tile(-1), *tiles, self._joker) if self._joker else (Tile(-1), *tiles)

    def __repr__(self) -> str:  # pragma: no cover
        props = {
            "numbers": self._numbers,
            "repeats": self._repeats,
            "colours": self._colours,
            "jokers": self._jokers,
            "min_len": self._min_len,
            "min_initial_value": self._min_initial_value,
            "solver_backend": self._solver.backend,
        }
        args = [f"{key}={value!r}" for key, value in props.items()]
        return f"RuleSet({', '.join(args)})"

    @property
    def numbers(self) -> Annotated[int, Interval(ge=1, le=26)]:
        """How many number tiles there are for each colour."""
        return self._numbers

    @property
    def repeats(self) -> Annotated[int, Interval(ge=1, le=4)]:
        """How many duplicates there are of each number tile."""
        return self._repeats

    @property
    def colours(self) -> Annotated[int, Interval(ge=1, le=8)]:
        """How many tile colours there are."""
        return self._colours

    @property
    def jokers(self) -> Annotated[int, Interval(ge=0, le=4)]:
        """How many joker tiles there are."""
        return self._jokers

    @property
    def min_len(self) -> Annotated[int, Interval(ge=2, le=6)]:
        """The minimum length of a valid set."""
        return self._min_len

    @property
    def min_initial_value(self) -> Annotated[int, Interval(ge=1, le=50)]:
        """The minimum value of tiles required for a player to make their first move."""
        return self._min_initial_value

    @property
    def tile_count(self) -> int:
        r"""Total number of unique tiles.

        This is equal to <code>[numbers][rummikub_solver.RuleSet.numbers] \*
        [colours][rummikub_solver.RuleSet.colours] +
        bool([jokers][rummikub_solver.RuleSet.jokers])</code>.

        """
        return self._tile_count

    @property
    def backend(self) -> MILPSolver:
        """The solver backend used for finding sets to place.

        This defaults to [`SCIPY`][rummikub_solver.MILPSolver.SCIPY], unless
        `highspy` installed, in which case the default is
        [`HIGHS`][rummikub_solver.MILPSolver.HIGHS].

        """
        return self._solver.backend

    @backend.setter
    def backend(self, backend: MILPSolver | None):
        from ._solver import RummikubSolver

        self._solver = RummikubSolver(self, backend)

    @cached_property
    def game_state_key(self) -> str:
        """Short string uniquely identifying game states that fit this ruleset.

        This key is useful when persisting game states, where you can then group
        persisted states by this key, and later on look up these states once a
        ruleset has been established.

        """
        # minimal initial value and minimum set length are not reflected in
        # the game state data so are not part of the key.
        keys = zip(
            "nrcj",
            (self._numbers, self._repeats, self._colours, self._jokers),
            strict=False,
        )
        return "".join([f"{k}{v}" for k, v in keys])

    @cached_property
    def tiles(self) -> Sequence[Tile]:
        """All valid tiles for this ruleset.

        Number tiles are arranged in numeric order per colour, with the first
        [`numbers`][rummikub_solver.RuleSet.numbers] entries the number tiles
        for the first [`Colour`][rummikub_solver.Colour], etc. If this ruleset
        contains jokers, then the last element of this sequence is the joker
        tile.
        """
        return self._tiles[1:]

    @cached_property
    def sets(self) -> Sequence[tuple[Tile, ...]]:
        """All valid sets of tiles for this ruleset."""
        return sorted(self._runs() | self._groups())

    @cached_property
    def set_values(self) -> Sequence[int]:
        ns, mlen = self._numbers, self._min_len
        # generate a runlength value matrix indexed by [len(set)][min(set)],
        # giving total tile value for a given set accounting for jokers. e.g. a
        # 3 tile run with lowest number 12 must have a joker acting as the 11 in
        # (j, 12, 13), and for initial placement the sum of numbers would be 36.
        rlvalues = [[0] * (ns + 1)]
        for i, _rl in enumerate(range(1, mlen * 2)):
            tiles = chain(range(i, ns + 1), repeat(ns - i))
            rlvalues.append([v + t for v, t in zip(rlvalues[-1], tiles, strict=False)])

        def _calc(
            s: tuple[int, ...],
            _next: Callable[[Iterator[int]], int] = next,
            _len: Callable[[Sized], int] = len,
            joker: int | None = self._joker,
        ) -> int:
            """Calculate sum of numeric value of tiles in set.

            If there are jokers in the set the max possible value for the run or
            group formed is used.

            """
            nums = ((t - 1) % ns + 1 for t in s if t != joker)
            try:
                n0 = _next(nums)
            except StopIteration:
                # a set of all jokers. Use length times max number value
                return _len(s) * ns
            try:
                # n0 == n1: group of same numbers, else run of same colour
                return _len(s) * n0 if n0 == _next(nums) else rlvalues[_len(s)][n0]
            except StopIteration:
                # len(nums) == 1, rest of set is jokers. Can be both a run or a
                # group, e.g. (5, j, j): (5, 5, 5) = 15 or (5, 6, 7) = 18, and
                # (13, j, j): (13, 13, 13) = 39 or (j, j, 13) = 36. Use max to
                # pick best.
                return max(_len(s) * n0, rlvalues[_len(s)][n0])

        return [_calc(set) for set in self.sets]

    def new_game(self) -> GameState:
        """Create a new game state for this ruleset.

        Returns:
            An empty game state.
        """
        return GameState(self._tiles)

    def _state_ideal_number_counts(self, state: GameState) -> Counter[int]:
        """Just the numeric values of the number tiles for a given game state.

        Any jokers are replaced with the next available highest number tile.

        """
        ncounts = Counter(state.rack)
        if self._joker:
            ncounts.pop(self._joker, None)
            numbers = cast(tuple[Number, ...], self._tiles[1:-1])
            for _ in range(state.rack[self._joker]):
                joker_value = self._numbers
                while joker_value:
                    if match := next(
                        (
                            t
                            for t in numbers[joker_value - 1 :: self._numbers]
                            if state.rack[t] < self._repeats
                        ),
                        None,
                    ):
                        ncounts[match] += 1
                        break
                    joker_value -= 1  # pragma: no cover

        return Counter({t.value for t in cast(Counter[Number], ncounts).elements()})

    def solve(
        self, state: GameState, mode: SolverMode | None = None
    ) -> ProposedSolution | None:
        """Find the best option for placing tiles from the rack.

        If no mode is selected, uses the game initial state flag to switch
        between [initial][rummikub_solver.SolverMode.INITIAL] and
        [tile-count][rummikub_solver.SolverMode.TILE_COUNT] modes.

        When in initial mode, if there are tiles on the table already,
        adds an extra round of solving if the minimal point threshold has
        been met, to find additional tiles that can be moved onto the
        table in the same turn.

        Provided the input game state modeled a valid rummikub game with a table
        that was [arrangeable][rummikub_solver.RuleSet.arrange_table] before
        this move, the tiles used in the solution sets plus any free jokers will
        equal the tiles on the table plus the tiles the proposed solution moves
        from the rack to the table.

        Args:
            state: The game state to solve.
            mode: Optional solver mode.

        Returns:
            The proposed solution if it is possible to put tiles on the table.

        Raises:
            ValueError: if the given state is [not valid][rummikub_solver.RuleSet.game_state_valid].

        """
        if not self.game_state_valid(state):
            raise ValueError(
                "Game state is not valid; either too many jokers or too many "
                "number tiles present"
            )
        if not state.rack:
            # no point in asking the solver
            return None

        if mode is None:
            mode = SolverMode.INITIAL if state.initial else SolverMode.TILE_COUNT

        if mode is SolverMode.INITIAL:
            ncounts = self._state_ideal_number_counts(state)
            if max(ncounts, default=0) >= self._min_initial_value:
                # when any single tile will do to reach the minimum initial
                # value, we can skip the initial mode altogether.
                mode = SolverMode.TILE_COUNT

            elif self._min_initial_value - sum(ncounts.elements()) > 0:
                # The rack doesn't have the tiles to form an initial meld
                return None

        sol = self._solver(mode, state)
        if not sol.tiles:
            return None

        tiles = sol.tiles
        set_indices = sol.set_indices

        if mode is SolverMode.INITIAL and state.table:
            # placed initial tiles, can now use rest of rack and what is
            # available on the table to look for additional tiles to place.
            new_state = state.with_move(*sol.tiles)
            stage2 = self._solver(SolverMode.TILE_COUNT, new_state)
            if stage2.tiles:
                tiles = sorted([*tiles, *stage2.tiles])
                set_indices = stage2.set_indices

        tmap, smap = self._tiles, self.sets
        prop = ProposedSolution(
            [tmap[t] for t in tiles], [smap[i] for i in set_indices]
        )

        # Catch corner cases by validating that the proposed sets include all
        # proposed tiles plus the table. If there are discrepancies, solve just
        # the table arrangement.
        if mode is SolverMode.INITIAL and Counter(
            chain.from_iterable(prop.sets)
        ) != state.table + Counter(prop.tiles):
            table_only = state.with_move(*prop.tiles).table_only()
            if arr := self._arrange_table(table_only):
                set_indices, free = arr
                prop = prop._replace(
                    sets=[smap[i] for i in set_indices], free_jokers=free
                )
            else:  # pragma: no cover
                # this should really only happen when the table state was not
                # arrangeable to begin with.
                _logger.warning("Backend failed to provide a full set solution")

        return prop

    def _arrange_table(self, table_only: GameState) -> tuple[Sequence[int], int] | None:
        joker, joker_count = self._joker, 0
        if joker:
            joker_count = table_only.table[joker]
            table_only.remove_table(*(joker,) * joker_count)

        for jc in range(joker_count + 1):
            if jc:
                assert joker is not None
                table_only.add_table(joker)
            sol = self._solver(SolverMode.TILE_COUNT, table_only)
            if sol.set_indices:
                return sol.set_indices, joker_count - jc

        return None

    def arrange_table(self, state: GameState) -> TableArrangement | None:
        """Check if the tiles on the table can be arranged into sets.

        Produces a series of sets and how many unattached jokers are available.

        Args:
            state: The game state for which to arrange the table tiles.

        Returns:
            The table arrangement if one can be determined.

        Raises:
            ValueError: if the given state is [not valid][rummikub_solver.RuleSet.game_state_valid].

        """
        table_only = state.table_only()
        if not self.game_state_valid(table_only):
            raise ValueError(
                "Table portion of game state is not valid; either too many "
                "jokers or too many number tiles present"
            )

        if arr := self._arrange_table(table_only):
            set_indices, free = arr
            return TableArrangement([self.sets[s] for s in set_indices], free)

        return None

    def game_state_valid(self, state: GameState) -> bool:
        """Validate a game state against this ruleset.

        Checks if the number of tiles in the game state are still legal within the ruleset;
        that is, the number of repeated tiles doesn't exceed the ruleset limits.

        Args:
            state: The game state to validate.

        Returns:
            Whether or not the state is valid.

        """
        state_tiles = state.rack + state.table
        trange = range(1, self._tile_count + 1)
        if any(t not in trange for t in state_tiles):  # pragma: no cover
            return False
        if self._joker and state_tiles.pop(self._joker, 0) > self._jokers:
            return False
        return max(state_tiles.values(), default=0) <= self._repeats

    def _runs(self) -> set[tuple[Tile, ...]]:
        cs, ns = range(self._colours), self._numbers
        lengths = range(self._min_len, self._min_len * 2)
        # runs start at a given coloured tile, and are between min_len and
        # 2x min_len (exclusive) tiles long.
        series = (
            range(ns * c + num, ns * c + num + length)
            for c, length in product(cs, lengths)
            for num in range(1, ns - length + 2)
        )
        tmap = self._tiles
        return self._combine_with_jokers(
            ([tmap[t] for t in s] for s in series), runs=True
        )

    def _groups(self) -> set[tuple[Tile, ...]]:
        ns, cs = self._numbers, self._colours
        # groups are between min_len and #colours long, a group per possible
        # tile number value.
        lengths = range(self._min_len, cs + 1)
        fullgroups = (range(num, ns * cs + 1, ns) for num in range(1, ns + 1))
        groups = chain.from_iterable(
            combinations(fg, len) for fg, len in product(fullgroups, lengths)
        )
        tmap = self._tiles
        return self._combine_with_jokers([tmap[t] for t in g] for g in groups)

    def _combine_with_jokers(
        self, sets: Iterable[Sequence[Tile]], runs: bool = False
    ) -> set[tuple[Tile, ...]]:
        j, mlen = self._joker, self._min_len
        if j is None:
            return set(map(tuple, sets))
        # for sets of minimum length: combine with jokers; any combination of
        # tokens in the original series replaced by any number of possible
        # jokers. For groups, do not generate further combinations for longer sets, as
        # these would leave jokers free for the next player to take. For runs
        # only generate 'inner' jokers.
        longer: Callable[[Sequence[Tile]], Iterable[tuple[Tile, ...]]] = lambda s: [  # noqa: E731
            tuple(s)
        ]
        if runs:
            longer = (  # noqa: E731
                lambda s: (
                    (s[0], *c, s[-1]) for c in combinations([*s[1:-1], *js], len(s) - 2)
                )
            )
        js = [j] * self._jokers
        comb = (
            combinations([*s, *js], len(s)) if len(s) == mlen else longer(s)
            for s in sets
        )
        return set(chain.from_iterable(comb))
