import json as jsonlib
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from typing import Any, Generic, TypeVar, cast, final
from weakref import WeakValueDictionary

from soialib.impl.function_maker import Expr, LineSpan, make_function
from soialib.impl.type_adapter import TypeAdapter
from soialib.never import Never

T = TypeVar("T")


@final
class Serializer(Generic[T]):
    __slots__ = (
        "__weakref__",
        "_adapter",
        "_to_dense_json_fn",
        "_to_readable_json_fn",
        "_from_json_fn",
    )

    _adapter: TypeAdapter
    _to_dense_json_fn: Callable[[T], Any]
    _to_readable_json_fn: Callable[[T], Any]
    _from_json_fn: Callable[[Any], T]

    def __init__(self, adapter: Never):
        # Use Never (^) as a trick to make the constructor internal.
        object.__setattr__(self, "_adapter", adapter)
        object.__setattr__(
            self, "_to_dense_json_fn", _make_to_json_fn(adapter, readable=False)
        )
        object.__setattr__(
            self,
            "_to_readable_json_fn",
            _make_to_json_fn(adapter, readable=True),
        )
        object.__setattr__(self, "_from_json_fn", _make_from_json_fn(adapter))

    def to_json(self, input: T, *, readable=False) -> Any:
        if readable:
            return self._to_readable_json_fn(input)
        else:
            return self._to_dense_json_fn(input)

    def to_json_code(self, input: T, readable=False) -> str:
        if readable:
            return jsonlib.dumps(self._to_readable_json_fn(input), indent=2)
        else:
            return jsonlib.dumps(self._to_dense_json_fn(input), separators=(",", ":"))

    def from_json(self, json: Any) -> T:
        return self._from_json_fn(json)

    def from_json_code(self, json_code: str) -> T:
        return self._from_json_fn(jsonlib.loads(json_code))

    def __setattr__(self, name: str, value: Any):
        raise FrozenInstanceError(self.__class__.__qualname__)

    def __delattr__(self, name: str):
        raise FrozenInstanceError(self.__class__.__qualname__)


# A cache to make sure we only create one Serializer for each TypeAdapter.
_type_adapter_to_serializer: WeakValueDictionary[TypeAdapter, Serializer] = (
    WeakValueDictionary()
)


def make_serializer(adapter: TypeAdapter) -> Serializer:
    return _type_adapter_to_serializer.setdefault(
        adapter, Serializer(cast(Never, adapter))
    )


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
