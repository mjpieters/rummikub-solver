# SPDX-License-Identifier: MIT
"""Hypothesis strategies for rulesets and game states."""

from collections import Counter
from itertools import chain, groupby
from typing import TypedDict

from hypothesis import database, settings
from hypothesis import strategies as st

from rummikub_solver import GameState, RuleSet, Tile

# On GitHub, save examples between runs (which are then cached)
settings.register_profile(
    "ci",
    parent=settings.get_profile("ci"),
    database=database.DirectoryBasedExampleDatabase(".hypothesis/examples"),
)


class RuleSetParams(TypedDict):
    numbers: int
    repeats: int
    colours: int
    jokers: int
    min_len: int
    min_initial_value: int


@st.composite
def ruleset_parameters(draw: st.DrawFn) -> RuleSetParams:
    numbers = draw(st.integers(2, 26))
    repeats = draw(st.integers(1, 4))
    colours = draw(st.integers(2, 8))
    jokers = draw(st.integers(0, 4))
    min_len = draw(st.integers(2, min(colours, numbers, 6)))
    min_initial_value = draw(st.integers(1, 50))

    return RuleSetParams(
        numbers=numbers,
        repeats=repeats,
        colours=colours,
        jokers=jokers,
        min_len=min_len,
        min_initial_value=min_initial_value,
    )


@st.composite
def rulesets(draw: st.DrawFn) -> RuleSet:
    return RuleSet(**draw(ruleset_parameters()))


@st.composite
def unique_tiles(
    draw: st.DrawFn, *, ruleset: RuleSet, exclude: Counter[Tile] | None = None
) -> list[Tile]:
    tiles = Counter(chain.from_iterable(ruleset.tiles for _ in range(ruleset.repeats)))
    if ruleset.jokers:
        tiles[ruleset.tiles[-1]] = ruleset.jokers
    if exclude:
        tiles -= exclude
    if not tiles:
        return []

    # add a repeat index to each tile so we can draw between 0 and ruleset.repeats
    # number tiles and between 0 and ruleset.jokers joker tiles.
    with_index = [it for _, g in groupby(tiles.elements()) for it in enumerate(g)]

    def _remove_index(index_and_tile_list: list[tuple[int, Tile]]) -> list[Tile]:
        return [tile for _, tile in index_and_tile_list]

    return draw(
        st.lists(st.sampled_from(with_index), max_size=tiles.total(), unique=True)
        .map(_remove_index)
        .map(sorted)
    )


@st.composite
def game_states(
    draw: st.DrawFn, *, ruleset: RuleSet, table_only: bool = False
) -> GameState:
    game = ruleset.new_game()
    game.add_table(*draw(unique_tiles(ruleset=ruleset)))
    if not table_only:
        game.add_rack(*draw(unique_tiles(ruleset=ruleset, exclude=game.table)))
    game.initial = draw(st.booleans())

    return game


@st.composite
def rulesets_and_game_states(
    draw: st.DrawFn, table_only: bool = False
) -> tuple[RuleSet, GameState]:
    ruleset = draw(rulesets())
    return ruleset, draw(game_states(ruleset=ruleset, table_only=table_only))
