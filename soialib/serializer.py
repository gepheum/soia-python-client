import json as jsonlib
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from typing import Any, Generic, TypeVar, cast, final

from soialib.impl.function_maker import Expr, LineSpan, make_function
from soialib.impl.type_adapter import TypeAdapter
from soialib.never import Never

T = TypeVar("T")


@final
class Serializer(Generic[T]):
    __slots__ = (
        "_to_dense_json_fn",
        "_to_readable_json_fn",
        "_from_json_fn",
    )

    _to_dense_json_fn: Callable[[T], Any]
    _to_readable_json_fn: Callable[[T], Any]
    _from_json_fn: Callable[[Any], T]

    def __init__(self, adapter: Never):
        # Use Never (^) as a trick to make the constructor internal.
        object.__setattr__(
            self, "_to_dense_json_fn", _make_to_json_fn(adapter, readable=False)
        )
        object.__setattr__(
            self,
            "_to_readable_json_fn",
            _make_to_json_fn(adapter, readable=True),
        )
        object.__setattr__(self, "_from_json_fn", _make_from_json_fn(adapter))

    def to_json(self, input: T, readable_flavor=False) -> Any:
        if readable_flavor:
            return self._to_readable_json_fn(input)
        else:
            return self._to_dense_json_fn(input)

    def to_json_code(self, input: T, readable_flavor=False) -> str:
        return jsonlib.dumps(self.to_json(input, readable_flavor))

    def from_json(self, json: Any) -> T:
        return self._from_json_fn(json)

    def from_json_code(self, json_code: str) -> T:
        return self._from_json_fn(jsonlib.loads(json_code))

    def __setattr__(self, name: str, value: Any):
        raise FrozenInstanceError(self.__class__.__qualname__)

    def __delattr__(self, name: str):
        raise FrozenInstanceError(self.__class__.__qualname__)


def make_serializer(adapter: TypeAdapter) -> Serializer:
    return Serializer(cast(Never, adapter))


def _make_to_json_fn(adapter: TypeAdapter, readable: bool) -> Callable[[Any], Any]:
    return make_function(
        name="to_json",
        params=["input"],
        body=[
            LineSpan.join(
                "return ",
                adapter.to_json_expr(
                    adapter.to_frozen_expr(Expr.join("input")),
                    readable=readable,
                ),
            ),
        ],
    )


def _make_from_json_fn(adapter: TypeAdapter) -> Callable[[Any], Any]:
    return make_function(
        name="from_json",
        params=["json"],
        body=[
            LineSpan.join("return ", adapter.from_json_expr(Expr.join("json"))),
        ],
    )
