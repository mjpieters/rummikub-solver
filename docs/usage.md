# Usage

This library models the playing rack for a single Rummikub player, together with
the tiles already played on the table. From this information it can then provide
possible moves to play.

## Rulesets and tiles

To generate solutions, you first need to create an instance of the [`RuleSet` class][rummikub_solver.RuleSet]. This lets you define how many numbers there are on the tiles you play with, how many different tile colours there are, if you are playing with jokers, and how many, etc.

The default configuration matches that of the default (Sabra rules) Rummikub game:

```python
from rummikub_solver import RuleSet

ruleset = RuleSet()
```

Within the confines of a ruleset there are a number of unique tiles. Most of these will be [`Number` tiles][rummikub_solver.Number], but there can also be [`Joker` tiles][rummikub_solver.Joker].

The number tiles have human-readable attributes: a numeric value and a colour. The joker, if present in the ruleset, is always the last element of the [`tiles` sequence][rummikub_solver.RuleSet.tiles]:

```pycon
>>> from rummikub_solver import RuleSet
>>> ruleset = RuleSet()
>>> black_6, red_4 = ruleset.tiles[5], ruleset.tiles[42]
>>> print(black_6, black_6.colour, black_6.value, sep=" - ")
<Black 6 (6)> - Colour.BLACK - 6
>>> print(red_4, red_4.colour, red_4.value, sep=" - ")
<Red 4 (43)> - Colour.RED - 4
>>> joker = ruleset.tiles[-1]
>>> print(joker)
<Joker (53)>
```

While all library methods that accept `Tile` objects also accept integers, using
the `Tile` subclasses makes it easier to connect, say, a user interface to this
library.

The tiles are always listed in their numeric order, by colour, with the colour
order dictated by the [`Colour` enum][rummikub_solver.Colour]. If you are building
a user-interface for Rummikub games, you will have to map your own representation
of tiles to these objects or the integer numbers they represent.

In further examples in this documentation, the tiles are often simply grouped by
colour based on the knowledge that the standard ruleset has 13 number tiles for
each colour.

## Game states

From a ruleset you can create new [`GameState` instances][rummikub_solver.GameState]:

```python
game = ruleset.new_game()
```

[`GameState`][rummikub_solver.GameState] models the state of a Rummikub game
from the perspective of a single player. It tracks three pieces of information:
what tiles are on the table already, what tiles are on the player's rack, and if
the player has made their initial move yet.

You can add and remove tiles from both the rack and the table:

```pycon
>>> from rummikub_solver import RuleSet
>>> ruleset = RuleSet()
>>> game = ruleset.new_game()
>>> black = ruleset.tiles[:13]
>>> blue = ruleset.tiles[13:26]
>>> orange = ruleset.tiles[26:39]
>>> red = ruleset.tiles[39:52]
>>> joker = ruleset.tiles[-1]
>>> game.add_rack(
...     black[9], black[11], black[12], red[2], red[3], red[10], red[12],
...     orange[1], red[1], blue[1], blue[7], blue[7], orange[8], blue[8],
... )
>>> game.add_table(black[10], orange[10], red[10], joker)
>>> game.remove_table(joker)
```

You can then introspect their states as either a counter or a sorted list:

```pycon
>>> game.table
Counter({<Black 11 (11)>: 1, <Orange 11 (37)>: 1, <Red 11 (50)>: 1})
>>> from pprint import pp
>>> pp(game.sorted_rack)
[<Black 10 (10)>,
 <Black 12 (12)>,
 <Black 13 (13)>,
 <Blue 2 (15)>,
 <Blue 8 (21)>,
 <Blue 8 (21)>,
 <Blue 9 (22)>,
 <Orange 2 (28)>,
 <Orange 9 (35)>,
 <Red 2 (41)>,
 <Red 3 (42)>,
 <Red 4 (43)>,
 <Red 11 (50)>,
 <Red 13 (52)>]
```

You can also set the [`GameState.initial`
flag][rummikub_solver.GameState.initial]; when this flag is `True` it indicates
that the player has not yet placed their initial move[^1].

!!! note "The `initial` flag is never automatically set for you!"

    Unless you use the [`GameState.with_move()`
    method][rummikub_solver.GameState.with_move], you are responsible for updating
    the `initial` flag yourself, the library doesn't apply proposed solutions to the
    game state directly so can't distinguish between an opening move having been
    made and other state updates.

## Finding legal table arrangements

Once you have reached a suitable game state, you can validate tiles on the table
by calling the [`RuleSet.arrange_table()`
method][rummikub_solver.RuleSet.arrange_table] and passing in the game state:

```pycon
>>> ruleset.arrange_table(game)
TableArrangement(sets=[(<Black 11 (11)>, <Orange 11 (37)>, <Red 11 (50)>)], free_jokers=0)
```

The method returns either a [`TableArrangement`
instance][rummikub_solver.TableArrangement], or `None` if there are no legal
combinations of sets possible with the present tiles:

```pycon
>>> game.remove_table(black[10])
>>> ruleset.arrange_table(game) is None
True
>>> game.add_table(black[10])
```

The arrangement provided is not necessarily the only legal arrangement of the tiles on the table; there can be other solutions, but only one will be returned.

The arrangement's [`free_jokers` attribute][rummikub_solver.TableArrangement.sets] tells you how many of the jokers on the table (if any) are _free_, in that they are not required for a legal table arrangement. These jokers can be used by the next player to form new sets with their tiles without having to substitute the joker first.

[^1]: Under normal Rummikub rules, a player can only combine tiles from their
rack with those already on the table once they have made an opening move worth
30 points just with the tiles from their rack, and when `initial` is true the
player has not yet done this.

## Finding legal player moves

To find the best combinations of tiles for a player to move from their rack to the table, you can use the [`RuleSet.solve()` method][rummikub_solver.RuleSet.solve] and pass in the game state; this method returns `None` if no moves are possible:

```pycon
>>> ruleset.solve(game) is None
True
>>> game.add_rack(black[10])
>>> sol = ruleset.solve(game)
>>> sol
ProposedSolution(tiles=[<Black 10 (10)>, <Black 11 (11)>, <Black 12 (12)>, <Black 13 (13)>, <Blue 2 (15)>, <Orange 2 (28)>, <Red 2 (41)>], sets=[(<Black 10 (10)>, <Black 11 (11)>, <Black 12 (12)>, <Black 13 (13)>), (<Black 11 (11)>, <Orange 11 (37)>, <Red 11 (50)>), (<Blue 2 (15)>, <Orange 2 (28)>, <Red 2 (41)>)], free_jokers=0)
>>> sol.tiles
[<Black 10 (10)>, <Black 11 (11)>, <Black 12 (12)>, <Black 13 (13)>, <Blue 2 (15)>, <Orange 2 (28)>, <Red 2 (41)>]
>>> pp(sol.sets)
[(<Black 10 (10)>, <Black 11 (11)>, <Black 12 (12)>, <Black 13 (13)>),
 (<Black 11 (11)>, <Orange 11 (37)>, <Red 11 (50)>),
 (<Blue 2 (15)>, <Orange 2 (28)>, <Red 2 (41)>)]
```

A possible solution is returned as a [`ProposedSolution`
instance][rummikub_solver.ProposedSolution]; it lists the tiles that should be
moved from the rack to the table, as well as _all_ the resulting sets on the
table.

The [`RuleSet.solve()` method][rummikub_solver.RuleSet.solve] can take a second
argument, `mode`, which takes a [`SolverMode` enum
member][rummikub_solver.SolverMode]. This lets you adjust the strategies used by
the solver.

### Initial move mode

When called with
[`mode=SolverMode.INITIAL`][rummikub_solver.SolverMode.INITIAL], the solver will
only look at the tiles on the rack to see if it can create a legal combination
that is equal to or higher than the [`RuleSet.min_initial_value`
value][rummikub_solver.RuleSet.min_initial_value]. If such a solution exists,
this is automatically followed by an additional round of solving to find any if
there are more tiles on the player rack that can be used to combine with tiles
on the table.

### Maximizing tile count

When using [`mode=SolverMode.TILE_COUNT`][rummikub_solver.SolverMode.TILE_COUNT]
the solver will optimize for the maximum number moved from the rack to the table.

### Maximizing tile value

With [`mode=SolverMode.TOTAL_VALUE`][rummikub_solver.SolverMode.TOTAL_VALUE],
the solver optimizes for a tile combination with the highest value. This can be
a useful strategy towards the end of a game where any tiles held by a losing
player count against them.

### Default solver mode

If you don't pass in a mode, the default is determined by the
[`initial` flag][rummikub_solver.GameState.initial] of the game state; when
`True` the default mode is
[`SolverMode.INITIAL`][rummikub_solver.SolverMode.INITIAL], otherwise it is
[`SolverMode.TILE_COUNT`][rummikub_solver.SolverMode.TILE_COUNT].
