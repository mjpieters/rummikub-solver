# SPDX-License-Identifier: MIT
from rummikub_solver import Colour, Joker, Number, Tile


def test_tile_repr() -> None:
    # only ever used as a dummy value in tile arrays position 0.
    assert repr(Tile(-1)) == "-"


def test_number_repr() -> None:
    assert repr(Number(42, Colour.MAGENTA, 7)) == "<Magenta 7 (42)>"


def test_joker_repr() -> None:
    assert repr(Joker(17)) == "<Joker (17)>"
