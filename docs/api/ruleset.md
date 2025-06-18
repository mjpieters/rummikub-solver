# Rulesets

The `RuleSet` is the starting point for solving Rummikub game problems. It
defines defines how many tiles are used in the game, how many different tile
colours there are, the number of jokers, etc.

```python
ruleset = RuleSet(colours=5, min_len=4, min_initial_value=42, jokers=3)
```

For a given [`GameState`][rummikub_solver.GameState], with tiles on the rack and / or the table, you can
then look for possible set placements:

```python
# A possible legal arrangement of tiles on the table
table_placement = ruleset.arrange_table(game)

# Can you place tiles from the rack on the table?
solution = ruleset.solve(game)
```


::: rummikub_solver.RuleSet