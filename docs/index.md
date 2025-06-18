# :material-cards-outline: Rummikub Solver library

A library to find possible moves for a Rummikub player given the tiles on their rack and the table.

## Features

- Can work with different Rummikub rules, letting you adjust the number of colours, tiles, and other aspects
- You can freely adjust what tiles are on the rack or on the table, within the limits of what tiles are available according to the current rules
- Can be used with any of the MILP solvers [supported by cvxpy](https://www.cvxpy.org/tutorial/solvers/index.html#choosing-a-solver).

## Installation

rummikub_solver is a Python package, so you can install it with your favorite Python package installer or dependency manager.

/// tab | :simple-python: pip
```console
$ pip install rummikub_solver
```

[pip](https://pip.pypa.io/en/stable/) is the main package installer for Python.
{: .result}
///

/// tab | :simple-astral: uv
```console
$ uv add rummikub_solver
```

[uv](https://docs.astral.sh/uv/) is an extremely fast Python package and project manager, written in Rust.
{: .result}
///

### Picking an alternative solver backend

--8<-- "README.md:picking_backend"

E.g. to include the HiGHS solver in your project, use:


/// tab | :simple-python: pip
```console
$ pip install rummikub_solver[highs]
```
///

/// tab | :simple-astral: uv
```console
$ uv add rummikub_solver[highs]
```
///

Pass in a specific [`MILPSolver`][rummikub_solver.MILPSolver] member when
constructing your [`RuleSet`][rummikub_solver.RuleSet] to specify what backend
to use.

!!! Warning

    This project is not being tested against the proprietary solver backends; they
    are included purely for completion's sake. Pull requests to address problems for
    specific proprietary backends are welcome, however.

#### Comparing backends

You can compare how well different backends perform by running the `test_full_game` test
in the project test suite, provided you enable pytest live logging:

1. Clone [this project][gh] from GitHub[^1].
2. Use the following command to run the specific test:

    ```console
    $ uv run \
      --extra BACKEND_EXTRA ... \
      --with OTHER_PYTHON_PACKAGE ... \
      pytest --log-cli-level INFO --no-cov \
        --solver-backend BACKEND ... \
        tests/test_full_game.py
    ```

    with as many `--extra BACKEND_EXTRA` and / or `--with OTHER_PYTHON_PACKAGE`
    switches as needed to install the desired backends (e.g. `--extra highs`
    would install the `HIGHS` backend into the uv-managed environment), and 
    with a `--solver-backend BACKEND` line for each 
    [`MILPSolver` member][rummikub_solver.MILPSolver] you want to compare.

The test simulates a full rummikub game between 3 players, playing the game
through from start to finish. It measures the performance of the solver at each
step and then outputs some statistics about that performance at the end. In a
single run of the test, all backends start with the same random seed, making the
performance of each solver directly comparable.

!!! Note

    A few rounds difference between solvers is to be expected as the failure of a
    solver to find a better solution may allow a different player to win earlier.

E.g. comparing the GLPK_MI, HIGHS, SCIP and SCIPY backends looks like this:

```console
$ uv run \
   --extra glpk_mi --extra highs --extra scip --extra cbc \
   pytest --log-cli-level INFO --no-cov \
     --solver-backend GLPK_MI --solver-backend HIGHS \
     --solver-backend SCIP --solver-backend SCIPY \
     --solver-backend CBC \
     tests/test_full_game.py
============================= test session starts ==============================
platform darwin -- Python 3.12.6, pytest-8.4.1, pluggy-1.6.0
Using --randomly-seed=1121915624
selected solver backends: CBC, GLPK_MI, HIGHS, SCIP, SCIPY
rootdir: /Users/martijn.pieters/Development/oss/rummikub_solver
configfile: pyproject.toml
plugins: randomly-3.16.0, cov-6.2.1, hypothesis-6.135.14
collected 5 items                                                              

tests/test_full_game.py::test_full_game[SCIPY] 
-------------------------------- live log call ---------------------------------
INFO     root:test_full_game.py:119 After 16 rounds, player 3 won the game
INFO     root:test_full_game.py:127 SCIPY solving stats across 35 calls:
  Time (mean ± δ):      16.6 ms ±   9.5 ms
  Range (min … max):     7.7 ms …  51.8 ms)
PASSED                                                                   [ 20%]
tests/test_full_game.py::test_full_game[GLPK_MI] 
-------------------------------- live log call ---------------------------------
INFO     root:test_full_game.py:119 After 16 rounds, player 3 won the game
INFO     root:test_full_game.py:127 GLPK_MI solving stats across 36 calls:
  Time (mean ± δ):       2.8 ms ±   1.4 ms
  Range (min … max):     1.2 ms …   6.3 ms)
PASSED                                                                   [ 40%]
tests/test_full_game.py::test_full_game[HIGHS] 
-------------------------------- live log call ---------------------------------
INFO     root:test_full_game.py:119 After 17 rounds, player 2 won the game
INFO     root:test_full_game.py:127 HIGHS solving stats across 37 calls:
  Time (mean ± δ):      12.0 ms ±   8.2 ms
  Range (min … max):     2.2 ms …  29.4 ms)
PASSED                                                                   [ 60%]
tests/test_full_game.py::test_full_game[CBC] 
-------------------------------- live log call ---------------------------------
INFO     root:test_full_game.py:119 After 10 rounds, player 3 won the game
INFO     root:test_full_game.py:127 CBC solving stats across 17 calls:
  Time (mean ± δ):       8.6 ms ±   4.5 ms
  Range (min … max):     5.6 ms …  21.1 ms)
PASSED                                                                   [ 80%]
tests/test_full_game.py::test_full_game[SCIP] 
-------------------------------- live log call ---------------------------------
INFO     root:test_full_game.py:119 After 17 rounds, player 1 won the game
INFO     root:test_full_game.py:127 SCIP solving stats across 37 calls:
  Time (mean ± δ):      40.6 ms ±  18.0 ms
  Range (min … max):    18.5 ms …  98.0 ms)
PASSED                                                                   [100%]
============================== 5 passed in 2.59s ===============================
```

!!! Info

    The timings shown are the mean, standard deviation, min and max duration of
    each call to `ruleset.solve()` **except** for those calls when the player
    has yet to complete their first move (`initial` is `True`). Initial moves
    are excluded because these require at least double the number of calls to
    the backend solver and so would unfairly skew the results.

The relative performance of each of the backends can readily change from one
release to the next, so any conclusions from the above example should be
re-reviewed if performance is important to you. As of the initial release of
`rummikub_solver`, `GLPK_MI` is the faster solver, but will not always find the
best solution when optimising for total value placed. `HIGHS` is a close second
in performance, but will do a better job at maximizing the total value of tiles.

[^1]: see [*Cloning a repository* ](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository#cloning-a-repository) for the GitHub help documentation on cloning.

[gh]: https://github.com/mjpieters/rummikub_solver
