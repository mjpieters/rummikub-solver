# SPDX-License-Identifier: MIT
import random
from typing import TYPE_CHECKING

import pytest

from rummikub_solver import GameState, MILPSolver, RuleSet

from .milp_solver_selection import *  # noqa: F403

if TYPE_CHECKING:
    # Define the (virtual) solver_backend fixture in type checking terms,
    # the actual parametrization is taken care of in a pytest_generate_tests() hook.

    @pytest.fixture
    def solver_backend() -> MILPSolver: ...


@pytest.fixture
def ruleset(solver_backend: MILPSolver) -> RuleSet:
    return RuleSet(solver_backend=solver_backend)


@pytest.fixture(params=(True, False), ids=("initial", "on-table"))
def game_state(request: pytest.FixtureRequest, ruleset: RuleSet) -> GameState:
    initial: bool = request.param

    game = ruleset.new_game()
    table_tiles = random.choices(ruleset.tiles, k=5)
    game.add_table(*table_tiles)
    rack_tiles = random.choices(ruleset.tiles, k=5)
    game.add_rack(*rack_tiles)
    game.initial = initial

    return game


@pytest.fixture
def in_progress_game(ruleset: RuleSet) -> GameState:
    """Reasonably complex table arrangement."""
    game = ruleset.new_game()
    tiles = ruleset.tiles
    # add zeroth tiles for 1-on-1 correspondence between index and tile number
    black, blue = (tiles[0], *tiles[:13]), (tiles[13], *tiles[13:26])
    orange, red = (tiles[26], *tiles[26:39]), (tiles[39], *tiles[39:62])
    joker = tiles[-1]

    game.add_table(
        *black[1:9],
        black[9],
        black[13],
        *blue[3:10],
        blue[5],
        *orange[2:5],
        orange[8],
        *orange[10:12],
        orange[13],
        red[5],
        *red[8:11],
        red[13],
        joker,
    )

    # rack tiles can't achieve the 30 point minimum
    game.add_rack(
        black[1],
        *black[3:5],
        black[10],
        black[13],
        blue[1],
        blue[2],
        blue[8],
        blue[10],
        blue[13],
        orange[3],
        orange[5],
        *orange[7:10],
        orange[7],
        orange[9],
        orange[12],
        orange[12],
        red[2],
        red[4],
        red[7],
        red[12],
    )

    return game
