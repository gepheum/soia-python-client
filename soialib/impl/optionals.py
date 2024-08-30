from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar
from weakref import WeakKeyDictionary

from soialib import spec
from soialib.impl.encoding import NULL_WIRE
from soialib.impl.function_maker import Expr, ExprLike
from soialib.impl.type_adapter import TypeAdapter

Other = TypeVar("Other")


def get_optional_adapter(other_adapter: TypeAdapter) -> TypeAdapter:
    return _other_adapter_to_optional_adapter.setdefault(
        other_adapter, _OptionalAdapter(other_adapter)
    )


@dataclass(frozen=True)
class _OptionalAdapter(TypeAdapter):
    __slots__ = ("other_adapter",)

    other_adapter: TypeAdapter

    def default_expr(self) -> ExprLike:
        return "None"

    def to_frozen_expr(self, arg_expr: ExprLike) -> Expr:
        return Expr.join(
            "(None if ",
            arg_expr,
            " is None else ",
            self.other_adapter.to_frozen_expr(arg_expr),
            ")",
        )

    def is_not_default_expr(self, arg_expr: ExprLike, attr_expr: ExprLike) -> Expr:
        return Expr.join(arg_expr, " is not None")

    def to_json_expr(self, in_expr: ExprLike, readable: bool) -> ExprLike:
        other_to_json = self.other_adapter.to_json_expr(in_expr, readable)
        if other_to_json == in_expr:
            return in_expr
        return Expr.join(
            "(None if ",
            in_expr,
            " is None else ",
            other_to_json,
            ")",
        )

    def from_json_expr(self, json_expr: ExprLike) -> ExprLike:
        other_from_json = self.other_adapter.from_json_expr(json_expr)
        if other_from_json == json_expr:
            return json_expr
        return Expr.join(
            "(None if ",
            json_expr,
            " is None else ",
            other_from_json,
            ")",
        )

    def finalize(
        self,
        resolve_type_fn: Callable[[spec.Type], "TypeAdapter"],
    ) -> None:
        self.other_adapter.finalize(resolve_type_fn)


_other_adapter_to_optional_adapter: WeakKeyDictionary[TypeAdapter, TypeAdapter] = (
    WeakKeyDictionary()
)
