# SPDX-License-Identifier: MIT
import logging
import random
import statistics
import time
from collections import Counter, deque
from itertools import chain

from rummikub_solver import GameState, Joker, RuleSet, SolverMode, Tile

_logger = logging.getLogger()


_SCALES: list[tuple[int, str]] = [
    (1000**i, u) for i, u in enumerate(("ns", "µs", "ms", "s"))
]


def _find_scale(nanoseconds: float) -> tuple[str, int]:
    assert nanoseconds > 0
    for scale, unit in reversed(_SCALES):
        if nanoseconds >= scale:
            return unit, scale
    raise AssertionError("unreachable")


def test_full_game(ruleset: RuleSet) -> None:
    """Play a random rummikub game between 3 players.

    This serves as a stress / regression test for each of the solver backends.

    For each test run, the mean, standard deviation, min and max durations of
    each solution run are shown, excluding the timings for initial moves (as
    these require at least double the number of calls to the solver).

    pytest-randomly ensures that within a test run, but with multiple MILPSolver
    backends selected, that this test starts with the same random seed for each
    of the backends. This makes the timing and number of steps used directly
    comparable between the backends.

    """
    # setup
    tiles = Counter(chain.from_iterable(ruleset.tiles for _ in range(ruleset.repeats)))
    joker = None
    if ruleset.jokers:
        joker = ruleset.tiles[-1]
        assert isinstance(joker, Joker)
        tiles[joker] = ruleset.jokers
    total_tiles = tiles.total()
    players = deque([ruleset.new_game() for _ in range(3)])
    table: Counter[Tile] = Counter()

    # deal 14 tiles to each player
    for player in players:
        initial_rack_tiles = random.sample(list(tiles.elements()), k=14)
        tiles -= Counter(initial_rack_tiles)
        player.add_rack(*initial_rack_tiles)

    durations: list[int] = []
    turn = 0
    turns_without_move = 0
    while all(p.rack for p in players):
        player = players[0] = players[0].with_table(*table.elements())

        # by using a the nested player_turn function here, pytest automatically captures
        # the context in case of failures.
        def player_turn(player: GameState, turn: int) -> bool:
            # if more than 4/5 of the tiles have been handed out, switch to total value optimisations
            mode = (
                None
                if player.initial or tiles.total() > (total_tiles // 5)
                else SolverMode.TOTAL_VALUE
            )
            start_ns = time.perf_counter_ns()
            solution = ruleset.solve(player, mode=mode)
            if not player.initial:
                durations.append(time.perf_counter_ns() - start_ns)

            if solution:
                initial = " as opening move" if player.initial else ""
                _logger.debug(
                    f"Round #{turn // 3 + 1}: Player {(turn % 3) + 1} is "
                    f"playing {len(solution.tiles)} tile(s){initial}"
                )
                assert Counter(solution.tiles) - player.rack == Counter()
                set_tiles = Counter(chain.from_iterable(solution.sets))
                if joker:
                    assert solution.free_jokers <= (
                        player.table[joker] + player.rack[joker]
                    )
                    set_tiles[joker] += solution.free_jokers
                assert set_tiles == table + Counter(solution.tiles)

                players[0] = player.with_move(*solution.tiles)
                table.update(solution.tiles)
            elif tiles:
                tile = random.choice(list(tiles.elements()))
                tiles[tile] -= 1
                player.add_rack(tile)
            else:
                return False

            return True

        # when there are no more tiles left, if all 3 players can't make moves
        # the game is tied.
        if player_turn(player, turn):
            turns_without_move = 0
        else:
            turns_without_move += 1

        if turns_without_move >= len(players):
            _logger.warning(f"Game was tied after {turn // 3 + 1} rounds.")
            return

        players.rotate(1)
        turn += 1

    _logger.info(
        f"After {(turn - 1) // 3 + 1} rounds, player {(turn - 1) % 3 + 1} won the game"
    )
    if len(durations) > 1:
        min_dur, max_dur = min(durations), max(durations)
        mean = statistics.mean(durations)
        std_dev = statistics.stdev(durations)
        unit, scale = _find_scale(mean)
        _logger.info(
            f"{ruleset.backend} solving stats across {len(durations)} calls:\n"
            f"  Time (mean ± δ):     {mean / scale:>5.1f} {unit:>2} ± {std_dev / scale:>5.1f} {unit:>2}\n"
            f"  Range (min … max):   {min_dur / scale:>5.1f} {unit:>2} … {max_dur / scale:>5.1f} {unit:>2})"
        )
    else:
        _logger.info("No durations available because a player won in the first round")
