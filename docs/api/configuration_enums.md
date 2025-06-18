# Configuration enums

## Solver operation modes

`SolverMode` is used to pick a specific solving approach when calling [`RuleSet.solve()`][rummikub_solver.RuleSet.solve].
::: rummikub_solver.SolverMode
    options:
        separate_signature: false



## Supported MILP solver backends

Each backend, with the exception of [`MILPSolver.SCIPY`] requires additional
packages to be installed. See [_Picking an alternative solver
backend_](../index.md#picking-an-alternative-solver-backend).

::: rummikub_solver.MILPSolver
    options:
        separate_signature: false
