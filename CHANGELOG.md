# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https:/keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- changes go below this line -->

## [1.1.0] - unreleased

- Upgrade `cvxpy` dependency to 1.8.1 or up, and `cvxopt` to 1.3.3 or up to
  ensure Python 3.14 compatibility. Note that individual solver backends may
  still have narrower requirements.
- Add Knitro (commercial solver) and cuOpt (GPU-accelerated solver) to backends.
  ([#140](https://github.com/mjpieters/rummikub-solver/issues/140),
   [#141](https://github.com/mjpieters/rummikub-solver/issues/141)).

## [1.0.0] - 2025-06-28

### Changed

- Minor update to the documentation to include some algorithm background.

## [1.0.0rc2] - 2025-06-27

### Changed

- Defer importing cvxpy until a ruleset is created or we need to list supported backends.

## [1.0.0rc1] - 2025-06-26

### Added

- First public release. This project was extracted from [`RummikubConsole`](https://github.com/mjpieters/RummikubConsole).
- Full documentation, tests and linting added.
- A slew of bugfixes and improvements.
