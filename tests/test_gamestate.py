# SPDX-License-Identifier: MIT
import pickle
import random
from collections import Counter

import pytest

from rummikub_solver import GameState, RuleSet


class TestGameState:
    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        ruleset = RuleSet()
        self.game = ruleset.new_game()
        self.tiles = ruleset.tiles

    def test_initial(self) -> None:
        assert self.game.initial is True
        self.game.initial = False
        assert self.game.initial is False

    def test_add_rack(self) -> None:
        tiles = random.choices(self.tiles, k=5)
        self.game.add_rack(*tiles)
        assert self.game.sorted_rack == sorted(tiles)
        assert self.game.rack == Counter(tiles)

    def test_add_rack_empty(self) -> None:
        self.game.add_rack()
        assert self.game.sorted_rack == []
        assert self.game.rack == Counter()

    def test_remove_rack(self) -> None:
        tiles = random.choices(self.tiles, k=5)
        self.game.add_rack(*tiles)

        to_remove = random.sample(tiles, k=2)
        self.game.remove_rack(*to_remove)
        expected = tiles
        for tile in to_remove:
            expected.remove(tile)
        assert self.game.sorted_rack == sorted(expected)
        assert self.game.rack == Counter(expected)

    def test_remove_rack_non_existent(self) -> None:
        *tiles, to_remove = random.sample(self.tiles, k=6)
        self.game.add_rack(*tiles)

        existing = random.choice(tiles)
        tiles.remove(existing)
        self.game.remove_rack(to_remove, existing)
        assert self.game.sorted_rack == sorted(tiles)
        assert self.game.rack == Counter(tiles)

    def test_remove_rack_empty(self) -> None:
        tiles = random.choices(self.tiles, k=5)
        self.game.add_rack(*tiles)

        self.game.remove_rack()
        assert self.game.sorted_rack == sorted(tiles)
        assert self.game.rack == Counter(tiles)

    def test_add_table(self) -> None:
        tiles = random.choices(self.tiles, k=5)
        self.game.add_table(*tiles)
        assert self.game.sorted_table == sorted(tiles)
        assert self.game.table == Counter(tiles)

    def test_add_table_empty(self) -> None:
        self.game.add_table()
        assert self.game.sorted_table == []
        assert self.game.table == Counter()

    def test_remove_table(self) -> None:
        tiles = random.choices(self.tiles, k=5)
        self.game.add_table(*tiles)

        to_remove = random.sample(tiles, k=2)
        self.game.remove_table(*to_remove)
        expected = tiles
        for tile in to_remove:
            expected.remove(tile)
        assert self.game.sorted_table == sorted(expected)
        assert self.game.table == Counter(expected)

    def test_remove_table_non_existent(self) -> None:
        *tiles, to_remove = random.sample(self.tiles, k=6)
        self.game.add_table(*tiles)

        existing = random.choice(tiles)
        tiles.remove(existing)
        self.game.remove_table(to_remove, existing)
        assert self.game.sorted_table == sorted(tiles)
        assert self.game.table == Counter(tiles)

    def test_remove_table_empty(self) -> None:
        tiles = random.choices(self.tiles, k=5)
        self.game.add_table(*tiles)

        self.game.remove_table()
        assert self.game.sorted_table == sorted(tiles)
        assert self.game.table == Counter(tiles)

    def test_reset(self) -> None:
        tiles = random.choices(self.tiles, k=5)
        self.game.add_rack(*tiles)
        tiles = random.choices(self.tiles, k=5)
        self.game.add_table(*tiles)
        self.game.initial = False

        self.game.reset()

        assert not self.game.rack
        assert not self.game.table
        assert self.game.initial

    @pytest.mark.parametrize("initial", (True, False))
    def test_with_move(self, initial: bool) -> None:
        table_tiles = random.choices(self.tiles, k=5)
        self.game.add_table(*table_tiles)
        rack_tiles = random.choices(self.tiles, k=5)
        self.game.add_rack(*rack_tiles)
        self.game.initial = initial

        to_move = random.sample(rack_tiles, k=3)
        expected_table = Counter(table_tiles) + Counter(to_move)
        expected_rack = Counter(rack_tiles) - Counter(to_move)

        new_state = self.game.with_move(*to_move)

        assert new_state.table == expected_table
        assert new_state.rack == expected_rack
        assert not new_state.initial

    def test_with_invalid_move(self) -> None:
        rack_tiles = random.sample(self.tiles, k=8)
        to_move, rack_tiles = rack_tiles[:3], rack_tiles[3:]
        self.game.add_rack(*rack_tiles)

        table_tiles = random.choices(self.tiles, k=5)
        self.game.add_table(*table_tiles)

        with pytest.raises(ValueError, match="Move includes tiles not on the rack"):
            self.game.with_move(*to_move)

    @pytest.mark.parametrize("initial", (True, False))
    def test_with_table(self, initial: bool) -> None:
        table_tiles = random.choices(self.tiles, k=5)
        self.game.add_table(*table_tiles)
        rack_tiles = random.choices(self.tiles, k=5)
        self.game.add_rack(*rack_tiles)
        self.game.initial = initial

        replacement_table = random.choices(self.tiles, k=5)
        expected_table = Counter(replacement_table)

        new_state = self.game.with_table(*replacement_table)

        assert new_state.table == expected_table
        assert new_state.rack == Counter(rack_tiles)
        assert new_state.initial == initial

    @pytest.mark.parametrize("initial", (True, False))
    def test_table_only(self, initial: bool) -> None:
        table_tiles = random.choices(self.tiles, k=5)
        self.game.add_table(*table_tiles)
        rack_tiles = random.choices(self.tiles, k=5)
        self.game.add_rack(*rack_tiles)
        self.game.initial = initial

        new_state = self.game.table_only()
        assert not new_state.rack
        assert new_state.table == Counter(table_tiles)
        assert new_state.initial == initial


def test_supports_pickling(game_state: GameState) -> None:
    data = pickle.dumps(game_state)
    unpickled = pickle.loads(data)
    assert game_state == unpickled
