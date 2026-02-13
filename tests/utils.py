from typing import Any


class either:
    def __init__(self, a: int, b: int) -> None:
        __tracebackhide__ = True
        self.a, self.b = sorted((a, b))

    def _repr_compare(self, other_side: Any) -> list[str]:
        return ["comparison failed", f"Obtained: {other_side}", f"Expected: {self}"]

    __hash__ = None  # pyright: ignore[reportAssignmentType]

    def __eq__(self, actual: Any) -> bool:
        return actual == self.a or actual == self.b

    def __repr__(self) -> str:
        return f"either({self.a}, {self.b})"

    def __contains__(self, value: Any) -> bool:
        return self.a <= value <= self.b
