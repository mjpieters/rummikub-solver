# SPDX-License-Identifier: MIT
from rummikub_solver._utils import extract_interval


def test_extract_interval() -> None:
    assert extract_interval("Annotated[int, Interval(ge=3, le=17)]") == range(3, 18)
    assert extract_interval("Annotated[int, Interval(ge=3, gt=2, le=17)]") is None
    assert extract_interval("MILPSolver | None") is None
