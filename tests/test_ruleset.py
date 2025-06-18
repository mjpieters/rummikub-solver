import logging
from collections import Counter
from itertools import chain

import pytest
from hypothesis import event, given, settings, target
from hypothesis import strategies as st

from rummikub_solver import (
    Colour,
    GameState,
    Joker,
    MILPSolver,
    Number,
    ProposedSolution,
    RuleSet,
    SolverMode,
)

from .hypothesis import (
    RuleSetParams,
    ruleset_parameters,
    rulesets,
    rulesets_and_game_states,
)

_logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "configuration,expected",
    (
        ({}, "n13r2c4j2"),
        ({"min_len": 4, "min_initial_value": 42}, "n13r2c4j2"),
        ({"numbers": 15, "repeats": 3, "colours": 6, "jokers": 1}, "n15r3c6j1"),
    ),
)
def test_game_state_key(configuration: RuleSetParams, expected: str) -> None:
    rs = RuleSet(**configuration)
    assert rs.game_state_key == expected


@pytest.mark.parametrize("with_jokers", (False, True))
def test_create_tile_maps(with_jokers: bool) -> None:
    expected = (
        Number(1, Colour.BLACK, 1),
        Number(2, Colour.BLACK, 2),
        Number(3, Colour.BLACK, 3),
        Number(4, Colour.BLACK, 4),
        Number(5, Colour.BLACK, 5),
        Number(6, Colour.BLUE, 1),
        Number(7, Colour.BLUE, 2),
        Number(8, Colour.BLUE, 3),
        Number(9, Colour.BLUE, 4),
        Number(10, Colour.BLUE, 5),
        Joker(11),
    )
    if not with_jokers:
        expected = expected[:-1]
    rs = RuleSet(numbers=5, colours=2, min_len=2, jokers=3 if with_jokers else 0)
    assert rs.tiles == expected


@pytest.mark.parametrize(
    "arguments,expected_message",
    (
        ({"numbers": -1}, "numbers=-1 must be in the range 2-26"),
        ({"numbers": 42}, "numbers=42 must be in the range 2-26"),
        ({"repeats": 0}, "repeats=0 must be in the range 1-4"),
        ({"colours": 17}, "colours=17 must be in the range 2-8"),
        ({"jokers": 11}, "jokers=11 must be in the range 0-4"),
        ({"min_len": 1}, "min_len=1 must be in the range 2-6"),
        ({"min_initial_value": 66}, "min_initial_value=66 must be in the range 1-50"),
        (
            {"numbers": 4, "colours": 4, "min_len": 5},
            "min_len=5 must be smaller than or equal to numbers=4",
        ),
        (
            {"numbers": 5, "colours": 4, "min_len": 5},
            "min_len=5 must be smaller than or equal to colours=4",
        ),
        (
            {
                "numbers": -1,
                "repeats": 0,
                "colours": 17,
                "jokers": 11,
                "min_len": 1,
                "min_initial_value": 66,
            },
            "numbers=-1 must be in the range 2-26",
        ),
    ),
)
def test_constructor_validates_interval(
    arguments: RuleSetParams, expected_message: str
) -> None:
    with pytest.raises(ValueError, match=expected_message):
        RuleSet(**arguments)


@settings(deadline=300)
@given(ruleset_parameters(), st.sampled_from(MILPSolver))
def test_properties(params: RuleSetParams, solver_backend: MILPSolver) -> None:
    rs = RuleSet(**params, solver_backend=solver_backend)
    assert rs.numbers == params["numbers"]
    assert rs.repeats == params["repeats"]
    assert rs.colours == params["colours"]
    assert rs.jokers == params["jokers"]
    assert rs.min_len == params["min_len"]
    assert rs.min_initial_value == params["min_initial_value"]
    assert rs.backend == solver_backend

    numbers, colours = params["numbers"], params["colours"]
    assert rs.tile_count == numbers * colours + bool(params["jokers"])
    assert len(rs.tiles) == rs.tile_count
    assert len({t.value for t in rs.tiles if isinstance(t, Number)}) == numbers
    assert len({t.colour for t in rs.tiles if isinstance(t, Number)}) == colours


@settings(deadline=300)
@given(rulesets())
def test_set_properties(rs: RuleSet) -> None:
    sets = rs.sets
    assert sets
    set_lengths = [len(s) for s in sets]
    assert all(
        rs.min_len <= sl < max(rs.colours + 1, 2 * rs.min_len) for sl in set_lengths
    )

    runs = [
        s
        for s in sets
        if (
            isinstance(s[0], Number)
            and isinstance(s[-1], Number)
            and s[0].colour == s[-1].colour
        )
    ]
    assert all(
        rs.min_len - rs.jokers
        <= len({t.value for t in run if isinstance(t, Number)})
        < 2 * rs.min_len
        for run in runs
    )
    assert all(
        len({t.colour for t in run if isinstance(t, Number)}) == 1 for run in runs
    )
    for run in runs:
        first = run[0]
        assert isinstance(first, Number)
        expected_diff = len(run) - 1
        while isinstance(last := run[expected_diff], Joker):
            expected_diff -= 1
        assert isinstance(last, Number)
        assert last.value - first.value == expected_diff
    assert all(
        isinstance(run[0], Number)
        and isinstance(run[-1], Number)
        and run[-1].value - run[0].value == len(run) - 1
        for run in runs
    )

    groups = [
        s
        for s in sets
        if (
            isinstance(s[0], Number)
            and isinstance(s[-1], Number)
            and s[0].colour != s[-1].colour
        )
    ]
    assert all(
        rs.min_len - rs.jokers
        <= len({t.colour for t in group if isinstance(t, Number)})
        <= rs.colours
        for group in groups
    )
    assert all(
        len({t.value for t in group if isinstance(t, Number)}) == 1 for group in groups
    )


def test_sets() -> None:
    assert RuleSet(numbers=3, colours=3, jokers=1).sets == [
        (
            Number(1, Colour.BLACK, 1),
            Number(2, Colour.BLACK, 2),
            Number(3, Colour.BLACK, 3),
        ),
        (Number(1, Colour.BLACK, 1), Number(2, Colour.BLACK, 2), Joker(10)),
        (Number(1, Colour.BLACK, 1), Number(3, Colour.BLACK, 3), Joker(10)),
        (
            Number(1, Colour.BLACK, 1),
            Number(4, Colour.BLUE, 1),
            Number(7, Colour.ORANGE, 1),
        ),
        (Number(1, Colour.BLACK, 1), Number(4, Colour.BLUE, 1), Joker(10)),
        (Number(1, Colour.BLACK, 1), Number(7, Colour.ORANGE, 1), Joker(10)),
        (Number(2, Colour.BLACK, 2), Number(3, Colour.BLACK, 3), Joker(10)),
        (
            Number(2, Colour.BLACK, 2),
            Number(5, Colour.BLUE, 2),
            Number(8, Colour.ORANGE, 2),
        ),
        (Number(2, Colour.BLACK, 2), Number(5, Colour.BLUE, 2), Joker(10)),
        (Number(2, Colour.BLACK, 2), Number(8, Colour.ORANGE, 2), Joker(10)),
        (
            Number(3, Colour.BLACK, 3),
            Number(6, Colour.BLUE, 3),
            Number(9, Colour.ORANGE, 3),
        ),
        (Number(3, Colour.BLACK, 3), Number(6, Colour.BLUE, 3), Joker(10)),
        (Number(3, Colour.BLACK, 3), Number(9, Colour.ORANGE, 3), Joker(10)),
        (
            Number(4, Colour.BLUE, 1),
            Number(5, Colour.BLUE, 2),
            Number(6, Colour.BLUE, 3),
        ),
        (Number(4, Colour.BLUE, 1), Number(5, Colour.BLUE, 2), Joker(10)),
        (Number(4, Colour.BLUE, 1), Number(6, Colour.BLUE, 3), Joker(10)),
        (Number(4, Colour.BLUE, 1), Number(7, Colour.ORANGE, 1), Joker(10)),
        (Number(5, Colour.BLUE, 2), Number(6, Colour.BLUE, 3), Joker(10)),
        (Number(5, Colour.BLUE, 2), Number(8, Colour.ORANGE, 2), Joker(10)),
        (Number(6, Colour.BLUE, 3), Number(9, Colour.ORANGE, 3), Joker(10)),
        (
            Number(7, Colour.ORANGE, 1),
            Number(8, Colour.ORANGE, 2),
            Number(9, Colour.ORANGE, 3),
        ),
        (Number(7, Colour.ORANGE, 1), Number(8, Colour.ORANGE, 2), Joker(10)),
        (Number(7, Colour.ORANGE, 1), Number(9, Colour.ORANGE, 3), Joker(10)),
        (Number(8, Colour.ORANGE, 2), Number(9, Colour.ORANGE, 3), Joker(10)),
    ]


def test_tablearrangement(ruleset: RuleSet, in_progress_game: GameState) -> None:
    tiles = ruleset.tiles
    # add zeroth tiles for 1-on-1 correspondence between index and tile number
    black, blue = (tiles[0], *tiles[:13]), (tiles[13], *tiles[13:26])
    orange, red = (tiles[26], *tiles[26:39]), (tiles[39], *tiles[39:62])
    joker = tiles[-1]

    arrangement = ruleset.arrange_table(in_progress_game)
    assert arrangement is not None
    assert arrangement.free_jokers == 0
    expected = [
        black[1:5],
        (black[5], blue[5], red[5]),
        black[6:10],
        (black[13], orange[13], red[13]),
        blue[3:7],
        blue[7:10],
        orange[2:5],
        (orange[8], orange[10], joker, orange[11]),
        red[8:11],
    ]
    if ruleset.backend is MILPSolver.CBC:
        # CBC is the only backend that moves the blue 6 from one run to the other
        expected[4:6] = [blue[3:6], blue[6:10]]

    assert arrangement.sets == expected


def test_illegal_tablearrangement(
    ruleset: RuleSet, in_progress_game: GameState
) -> None:
    # remove the joker that is in play
    in_progress_game.remove_table(ruleset.tiles[-1])

    arrangement = ruleset.arrange_table(in_progress_game)
    assert arrangement is None


# deadline is disabled to allow for slow backends such as SCIP to complete
@settings(deadline=None)
@given(rulesets_and_game_states(table_only=True))
def test_tablearrangement_hypothesis(
    solver_backend: MILPSolver, ruleset_game: tuple[RuleSet, GameState]
) -> None:
    ruleset, game = ruleset_game
    ruleset.backend = solver_backend

    target(game.table.total(), label="Number of tiles on the table")
    arrangement = ruleset.arrange_table(game)
    event(str(bool(arrangement)), payload="arrangement found?")
    if arrangement is not None:
        assert ruleset.game_state_valid(game)


class TestGameStateValid:
    @pytest.fixture(autouse=True)
    def _setup(self, ruleset: RuleSet, in_progress_game: GameState) -> None:
        self.ruleset = ruleset
        self.game = in_progress_game

    def test_valid_state(self) -> None:
        assert self.ruleset.game_state_valid(self.game)

        try:
            self.ruleset.solve(self.game)
        except ValueError as ex:
            raise AssertionError("Should not have raised a ValueError") from ex

        try:
            self.ruleset.arrange_table(self.game)
        except ValueError as ex:
            raise AssertionError("Should not have raised a ValueError") from ex

    def test_too_many_jokers(self) -> None:
        joker = self.ruleset.tiles[-1]
        self.game.add_rack(joker)
        self.game.add_table(joker)

        assert not self.ruleset.game_state_valid(self.game)

        with pytest.raises(
            ValueError,
            match=(
                "Game state is not valid; either too many jokers or too many "
                "number tiles present"
            ),
        ):
            self.ruleset.solve(self.game)

        # when disregarding the rack, the table counts are valid
        try:
            self.ruleset.arrange_table(self.game)
        except ValueError as ex:
            raise AssertionError("Should not have raised a ValueError") from ex

        # until we explicitly make just the table portion invalid
        self.game.add_table(joker)
        with pytest.raises(
            ValueError,
            match=(
                "Table portion of game state is not valid; either too many "
                "jokers or too many number tiles present"
            ),
        ):
            self.ruleset.arrange_table(self.game)

    def test_too_many_numbers(self) -> None:
        b1, b13 = self.ruleset.tiles[0], self.ruleset.tiles[12]
        self.game.add_rack(b1)

        assert not self.ruleset.game_state_valid(self.game)

        with pytest.raises(
            ValueError,
            match=(
                "Game state is not valid; either too many jokers or too many "
                "number tiles present"
            ),
        ):
            self.ruleset.solve(self.game)

        # when disregarding the rack, the table counts are valid
        try:
            self.ruleset.arrange_table(self.game)
        except ValueError as ex:
            raise AssertionError("Should not have raised a ValueError") from ex

        # until we explicitly make just the table portion invalid
        self.game.add_table(b13, b13)
        with pytest.raises(
            ValueError,
            match=(
                "Table portion of game state is not valid; either too many "
                "jokers or too many number tiles present"
            ),
        ):
            self.ruleset.arrange_table(self.game)


def assert_gamestate_solution_invariants(
    game: GameState, solution: ProposedSolution, table_valid: bool = True
) -> None:
    # all moved tiles came from the rack
    assert Counter(solution.tiles) - game.rack == Counter()

    proposed_set_tiles = Counter(chain.from_iterable(solution.sets))

    # Account for free jokers.
    if solution.free_jokers:
        joker = next(
            (t for t in chain(game.table, game.rack) if isinstance(t, Joker)), None
        )
        assert joker is not None
        # the free jokers must have been on the table or on the rack to begin with
        assert solution.free_jokers <= (game.table[joker] + game.rack[joker])
        proposed_set_tiles[joker] += solution.free_jokers

    # The proposed sets consist of tiles present on the table plus the
    # moved tiles, but only if the table was valid to begin with.
    if table_valid:
        assert proposed_set_tiles == game.table + Counter(solution.tiles)


@pytest.mark.parametrize("mode", (None, SolverMode.INITIAL))
def test_solve_initial(
    ruleset: RuleSet, in_progress_game: GameState, mode: SolverMode | None
) -> None:
    tiles = ruleset.tiles

    # initial move should not yet be possible
    solution = ruleset.solve(in_progress_game, mode=mode)
    assert solution is None, solution

    # but with an orange 10 it is possible to form an initial meld of more than 30 points
    in_progress_game.add_rack(tiles[35])  # orange 10
    solution = ruleset.solve(in_progress_game, mode=mode)

    assert solution is not None
    # while different backends may select different tiles, they should all maximize
    # the tile count and so find the same number. The exact sets differ based on
    # the tiles selected.
    assert len(solution.tiles) == 21
    assert solution.sets
    assert ruleset.arrange_table(in_progress_game.with_move(*solution.tiles))
    assert_gamestate_solution_invariants(in_progress_game, solution)


@pytest.mark.parametrize("mode", (None, SolverMode.TILE_COUNT))
def test_solve_tile_count(
    ruleset: RuleSet, in_progress_game: GameState, mode: SolverMode | None
) -> None:
    in_progress_game.initial = False

    solution = ruleset.solve(in_progress_game, mode=mode)
    assert solution is not None

    # while different backends may select different tiles, they should all maximize
    # the tile count and so find the same number. The exact sets differ based on
    # the tiles selected.
    assert len(solution.tiles) == 20
    assert solution.sets
    assert ruleset.arrange_table(in_progress_game.with_move(*solution.tiles))
    assert_gamestate_solution_invariants(in_progress_game, solution)


def test_solve_total_value(ruleset: RuleSet, in_progress_game: GameState) -> None:
    in_progress_game.initial = False

    solution = ruleset.solve(in_progress_game, mode=SolverMode.TOTAL_VALUE)
    assert solution is not None

    # backends may select different tiles, and differ in their ability to
    # maximize the total tile value, so we can, at best, include known values
    # for different solvers and use this as a range for any others. The exact
    # sets differ based on the tiles selected.
    expected_tile_sum = {
        MILPSolver.CBC: 515,
        # MILPSolver.GLPK_MI  is either 515 _or_ 589, depending on the exact version installed.
        MILPSolver.SCIPY: 515,
        MILPSolver.HIGHS: 589,
        MILPSolver.SCIP: 589,
    }
    if expected := expected_tile_sum.get(ruleset.backend):
        assert sum(solution.tiles) == expected
    else:
        actual = sum(solution.tiles)
        _logger.info(f"{ruleset.backend} produced a solution summing to {actual}")
        assert (
            min(expected_tile_sum.values()) <= actual <= max(expected_tile_sum.values())
        )
    assert solution.sets
    assert ruleset.arrange_table(in_progress_game.with_move(*solution.tiles))
    assert_gamestate_solution_invariants(in_progress_game, solution)


def test_solve_default_mode(ruleset: RuleSet, in_progress_game: GameState) -> None:
    # player has not yet moved, initial=True
    assert in_progress_game.initial is True
    solution = ruleset.solve(in_progress_game)
    assert solution is None

    # But if the player has moved, then the default is to maximize the tile count
    in_progress_game.initial = False
    solution = ruleset.solve(in_progress_game)
    assert solution is not None


# deadline is disabled to allow for slow backends such as SCIP to complete
@settings(deadline=None)
@given(rulesets_and_game_states(), st.sampled_from([None, *SolverMode]))
def test_solve_hypothesis(
    solver_backend: MILPSolver,
    ruleset_game: tuple[RuleSet, GameState],
    mode: SolverMode | None,
) -> None:
    ruleset, game = ruleset_game
    ruleset.backend = solver_backend

    target(game.rack.total(), label="Number of tiles on the rack")
    solution = ruleset.solve(game, mode=mode)
    event(str(bool(solution)), payload="solution found?")
    if solution is not None:
        table_valid = bool(ruleset.arrange_table(game) is not None)
        event(str(table_valid), payload="table state valid?")
        assert_gamestate_solution_invariants(game, solution, table_valid)
