# SPDX-License-Identifier: MIT
import ast
import inspect
import operator
from collections.abc import Callable
from enum import Enum
from functools import partial, wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def extract_interval(annotation: str) -> range | None:
    """Given a string Annotation[int, Interval(...)] extract the range."""
    try:
        expr = ast.parse(annotation).body[0]
    except (SyntaxError, AttributeError):  # pragma: no cover
        return None
    match expr:
        case ast.Expr(
            value=ast.Subscript(
                value=ast.Name(id="Annotated"),
                slice=ast.Tuple(
                    elts=[
                        ast.Name(id="int"),
                        ast.Call(func=ast.Name(id="Interval"), keywords=interval),
                    ]
                ),
            )
        ):
            pass
        case _:
            return None
    if len(interval) != 2:
        return None
    from_, to_ = interval
    assert from_.arg == "ge", "Extend _utils.extract_interval to handle gt"
    assert isinstance(from_.value, ast.Constant) and isinstance(from_.value.value, int)
    assert to_.arg == "le", "Extend _utils.extract_interval to handle le"
    assert isinstance(to_.value, ast.Constant) and isinstance(to_.value.value, int)
    return range(from_.value.value, to_.value.value + 1)


def validate_intervals(f: Callable[P, R]) -> Callable[P, R]:
    """Validate all interval annotations.

    To avoid an additional runtime dependency on the annotated_types package, this is done
    by parsing the expression into an AST.

    """
    sig = inspect.signature(f)
    ranges: dict[str, range] = {}
    for name, param in sig.parameters.items():
        ann = param.annotation
        if isinstance(ann, str) and (interval := extract_interval(ann)):
            ranges[name] = interval

    @wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        for name, value in kwargs.items():
            if (accepted := ranges.get(name)) and value not in accepted:
                raise ValueError(
                    f"{name}={value} must be in the range {accepted[0]}-{accepted[-1]}"
                )
        return f(*args, **kwargs)

    return wrapper


E = TypeVar("E", bound=Enum)


def enum_docstrings(enum: type[E]) -> type[E]:
    '''Attach docstrings to enum members.

    Docstrings are string literals that appear directly below the enum member
    assignment expression:

    ```
    @enum_docstrings
    class SomeEnum(Enum):
        """Docstring for the SomeEnum enum"""

        foo_member = "foo_value"
        """Docstring for the foo_member enum member"""

    SomeEnum.foo_member.__doc__  # 'Docstring for the foo_member enum member'
    ```

    '''
    try:
        mod = ast.parse(inspect.getsource(enum))
    except OSError:  # pragma: no cover
        # no source code available
        return enum

    if mod.body and isinstance(class_def := mod.body[0], ast.ClassDef):
        # An enum member docstring is unassigned if it is the exact same object
        # as enum.__doc__.
        unassigned = partial(operator.is_, enum.__doc__)
        names = enum.__members__.keys()
        member: E | None = None
        for node in class_def.body:
            match node:
                case ast.Assign(targets=[ast.Name(id=name)]) if name in names:
                    # Enum member assignment, look for a docstring next
                    member = enum[name]
                    continue

                case ast.Expr(value=ast.Constant(value=str(docstring))) if (
                    member and unassigned(member.__doc__)
                ):
                    # docstring immediately following a member assignment
                    member.__doc__ = docstring

                case _:
                    pass

            member = None

    return enum
