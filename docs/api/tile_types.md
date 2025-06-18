# Tile types

Tiles are the playing pieces in the Rummikub game. They are represented as
subclasses of `int`, and for a given [`RuleSet`][rummikub_solver.RuleSet], are
given a unique numeric value. This means tiles for one ruleset can't be used
with another.

All [`GameState`][rummikub_solver.GameState] methods that accept tiles, also
accept regular `int` values, these are automatically be mapped to their `Tile`
counterparts.

::: rummikub_solver.Tile
::: rummikub_solver.Number
::: rummikub_solver.Joker

## Tile colours

The [`Colour`][rummikub_solver.Colour] enum lists the colours used for tiles in
a [`RuleSet`][rummikub_solver.RuleSet]. E.g. the default ruleset configuration
uses 4 colours, so the first four members of this enum are used to represent the
colours. The actual colour value is abstract, red tiles work just the same as
green tiles, etc. You can treat these as opaque tokens just to keep tiles from
different colours apart.

::: rummikub_solver.Colour
    options:
        show_if_no_docstring: true
        separate_signature: false
        summary: false
