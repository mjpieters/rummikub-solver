From a given `RuleSet` you can create [`GameState`
instances][rummikub_solver.GameState], which track the state of the tile rack
and played tiles for a player:

```python
from rummikub_solver import RuleSet

ruleset = RuleSet()  # standard settings for a Sabra-rules Rummikub game
game = ruleset.new_game()

# add tiles to the rack
all_tiles = ruleset.tiles
black = all_tiles[:ruleset.numbers]
blue = all_tiles[ruleset.numbers:ruleset.numbers * 2]
orange = all_tiles[ruleset.numbers * 2:ruleset.numbers * 3]
red = all_tiles[ruleset.numbers * 3:ruleset.numbers * 4]
# a typical run of 14 random starter tiles
game.add_rack(
    black[9], black[11], black[12],    # black 10, 12 and 13 tiles
    red[2], red[3], red[10], red[12],  # red 3, 4, 11 and 12 tiles
    orange[1], red[1], blue[1],        # orange, red and blue 2 tiles
    blue[7], blue[7]                   # both the blue 8 tiles
    orange[8], blue[8]                 # orange and blue 9 tiles.
)
# player can't make a move, so picks a black 11 tile
game.add_rack(black[10])
# another player can make moves and placed tiles on the table
game.add_table(
    blue[0], blue[1], blue[2],         # blue 1, 2 and 3 tiles
    black[10], orange[10], red[10]     # black, orange and red 11 tiles
)
```

[`GameState` instances][rummikub_solver.GameState] are pickleable, to facilitate
saving a player's game state between sessions.

::: rummikub_solver.GameState
    options:
        merge_init_into_class: false
