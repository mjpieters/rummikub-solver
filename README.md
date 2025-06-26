[![PyPI version](https://img.shields.io/pypi/v/rummikub-solver)](https://pypi.python.org/project/rummikub-solver)
[![License](https://img.shields.io/pypi/l/rummikub-solver)](https://github.com/mjpieters/rummikub-solver/blob/main/LICENSE.txt)
![Python versions supported](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fmjpieters%2Frummikub-solver%2Fmain%2Fpyproject.toml)
[![Built with uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Checked with Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with Pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)
[![Built with Material for MkDocs](https://img.shields.io/badge/Material_for_MkDocs-526CFE?logo=materialformkdocs&label=&labelColor=grey&logoColor=white)](https://squidfunk.github.io/mkdocs-material/)
[![Python checks](https://github.com/mjpieters/rummikub-solver/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/mjpieters/rummikub-solver/actions/workflows/ci-cd.yml)
[![Coverage](https://codecov.io/gh/mjpieters/rummikub-solver/graph/badge.svg?token=ZRZO4XRBP6)](https://codecov.io/gh/mjpieters/rummikub-solver)


# Rummikub Solver library

A Rummikub solver library, written in Python, to find the best options for placing tiles from a player's rack on to the table.

The algorithm used builds on the approach described by D. Den Hertog, P. B. Hulshof (2006), "Solving Rummikub Problems by Integer Linear Programming", *The Computer Journal, 49(6)*, 665-669 ([DOI 10.1093/comjnl/bxl033](https://doi.org/10.1093/comjnl/bxl033)).

## Features

- Can work with different Rummikub variations, letting you adjust the number of colours, tiles, and other aspects
- You can freely adjust what tiles are on the rack or on the table, within the limits of what tiles are available according to the current rules
- Can be used with any of the Mixed-Integer Linear Programming (MILP) solvers [supported by cvxpy](https://www.cvxpy.org/tutorial/solvers/index.html#choosing-a-solver).

## Solver improvements

The original models described by Den Hertog and Hulshof assume that all possible sets that meet the minimum length requirements and can't be split up are desirable outcomes.

However, any group set (tiles with the same number but with different colours) containing at least one joker, but which is longer than the minimal run, in effect contains a redundant joker, something you wouldn't want to leave on the table for the next player to use. The same applies to run sets (tiles of the same colour but with consecutive numbers), that are longer than the minimal set length but start or end with a joker. In this implementation, such sets are omitted from
the possible options.

The implementation also includes a solver for the initial move, where you can only
use tiles from your own rack and must place a minimum amount of points before you
can use tiles already on the table. This solver is a variant of the original solver
that maximizes tiles placed, but is constrained by the minimal point amount and
_disregards_ jokers (which means jokers are only used for the opening meld if that is the only option available).

## Documentation

See the [project documentation][docs] for details.

## Install

You can install this project the usual way. e.g. with `pip`:

```console
$ pip install rummikub-solver
```

or with [uv][]:

```console
$ uv add rummikub-solver
```

### Picking an alternative solver backend

<!-- --8<-- [start:picking_backend] -->

This library builds on [cvxpy][] to define the Rummikub models, which can then be solved using any of the [supported MILP solver backends][cpsolvers]. By default, the `SCIPY` backend is used, which in turn uses a version of the [HiGHS optimizer][highs] that comes bundled with [SciPy][scipy].

You can also install an alternative Open Source solver backends via [extras][]:

| Extra | Backend | License |   |
| ----- | ------- | ------- | - |
| `cbc` | [COIN-OR](https://github.com/coin-or/Cbc) Branch-and-Cut solver | [EPL-2.0][epl-20] | |
| `glpk_mi` | [GNU Linear Programming Kit](https://www.gnu.org/software/glpk/) | [GPL-3.0-only][gpl-30-only] | Installs the [cvxopt project](https://pypi.org/p/cvxopt) |
| `highs` | [HiGHS][highs] | [MIT][mit] | Arguably the best OSS MILP solver available. This installs a newer version of HiGHS than what is bundled with SciPy. |
| `scip` | [SCIP](https://scipopt.org/) | [Apache-2.0][apache-20] | |

You can also pick from a number of commercial solvers; no extras are provided for these:

- `COPT`: Cardinal Optimizer, <https://github.com/COPT-Public/COPT-Release>
- `CPLEX`: IBM CPLEX, <https://www.ibm.com/docs/en/icos>
- `GUROBI`: Gurobi Optimizer, <https://www.gurobi.com/>
- `MOSEK`: <https://www.mosek.com/>
- `XPRESS`: Fico XPress,, <https://www.fico.com/en/products/fico-xpress-optimization>

Refer to their respective documentations for installation instructions.

When HiGHS is installed, it is automatically used as the default solver.

[scipy]: https://scipy.org/
[epl-20]: https://spdx.org/licenses/EPL-2.0.html
[gpl-30-only]: https://spdx.org/licenses/GPL-3.0-only.html
[mit]: https://spdx.org/licenses/MIT.html
[apache-20]: https://spdx.org/licenses/Apache-2.0.html
[cvxpy]: https://www.cvxpy.org
[cpsolvers]: https://www.cvxpy.org/tutorial/solvers/index.html#choosing-a-solver
[highs]: https://highs.dev/
[extras]: https://packaging.python.org/en/latest/tutorials/installing-packages/#installing-extras

<!-- --8<-- [end:picking_backend] -->

## Development

The source code for this project can be found [on GitHub][gh].

When running locally, install [uv][], then run:

```console
$ uv run rsconsole
```

to run the console solver. A [Taskfile](https://taskfile.dev/) is provided that defines specific tasks such as linting, formatting or previewing the documentation:

```console
$ task --list
task: Available tasks for this project:
* dev:format:         Runs formatters                                    (aliases: format)
* dev:lint:           Lint the source code                               (aliases: lint)
* dev:test:           Run tests                                          (aliases: test)
* dev:uv-lock:        Updates the uv lock file                           (aliases: lock)
* dist:build:         Build the distribution packages                    (aliases: dist)
* dist:clean:         Remove built distribution packages                 (aliases: clean)
* dist:publish:       Publish package to PyPI                            (aliases: publish)
* docs:serve:         Live preview server for project documentation      (aliases: preview)
```

## Credits

The initial version of the solver was written by [Ollie Hooper][oh].

This version is a complete rewrite by [Martijn Pieters][mp], to improve
performance and address shortcomings in the original paper.

[pipx]: https://pipxproject.github.io/
[uv]: https://docs.astral.sh/uv/
[docs]: https://rummikub-solver.readthedocs.io
[gh]: https://github.com/mjpieters/rummikub-solver
[oh]: https://github.com/Ollie-Hooper
[mp]: https://www.zopatista.com
