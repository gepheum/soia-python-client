from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final, final

from soialib import spec
from soialib.impl.function_maker import Expr, ExprLike
from soialib.impl.type_adapter import TypeAdapter
from soialib.timestamp import Timestamp


class AbstractPrimitiveAdapter(TypeAdapter):
    @final
    def finalize(
        self,
        resolve_type_fn: Callable[[spec.Type], "TypeAdapter"],
    ) -> None:
        pass


class _BoolAdapter(AbstractPrimitiveAdapter):
    def default_expr(self) -> ExprLike:
        return "False"

    def to_frozen_expr(self, arg_expr: ExprLike) -> Expr:
        return Expr.join("(True if ", arg_expr, " else False)")

    def is_not_default_expr(self, arg_expr: ExprLike, attr_expr: ExprLike) -> ExprLike:
        return arg_expr

    def to_json_expr(
        self,
        in_expr: ExprLike,
        readable: bool,
    ) -> ExprLike:
        if readable:
            return Expr.join("(1 if ", in_expr, " else 0)")
        else:
            return in_expr

    def from_json_expr(self, json_expr: ExprLike) -> Expr:
        return Expr.join("(True if ", json_expr, " else False)")


BOOL_ADAPTER: Final[TypeAdapter] = _BoolAdapter()


@dataclass(frozen=True)
class _AbstractIntAdapter(AbstractPrimitiveAdapter):
    """Type adapter implementation for int32, int64 and uint64."""

    def default_expr(self) -> ExprLike:
        return "0"

    def to_frozen_expr(self, arg_expr: ExprLike) -> Expr:
        return Expr.join("(", arg_expr, " | 0)")

    def is_not_default_expr(self, arg_expr: ExprLike, attr_expr: ExprLike) -> ExprLike:
        return arg_expr

    def to_json_expr(self, in_expr: ExprLike, readable: bool) -> ExprLike:
        return in_expr

    def from_json_expr(self, json_expr: ExprLike) -> Expr:
        return Expr.join("(", json_expr, " | 0)")


@dataclass(frozen=True)
class _Int32Adapter(_AbstractIntAdapter):
    pass


@dataclass(frozen=True)
class _Int64Adapter(_AbstractIntAdapter):
    pass


@dataclass(frozen=True)
class _Uint64Adapter(_AbstractIntAdapter):
    pass


INT32_ADAPTER: Final[TypeAdapter] = _Int32Adapter()
INT64_ADAPTER: Final[TypeAdapter] = _Int64Adapter()
UINT64_ADAPTER: Final[TypeAdapter] = _Uint64Adapter()


@dataclass(frozen=True)
class _AbstractFloatAdapter(AbstractPrimitiveAdapter):
    """Type adapter implementation for float32 and float64."""

    def default_expr(self) -> ExprLike:
        return "0.0"

    def to_frozen_expr(self, arg_expr: ExprLike) -> Expr:
        return Expr.join("(", arg_expr, " + 0.0)")

    def is_not_default_expr(self, arg_expr: ExprLike, attr_expr: ExprLike) -> ExprLike:
        return arg_expr

    def to_json_expr(self, in_expr: ExprLike, readable: bool) -> ExprLike:
        return in_expr

    def from_json_expr(self, json_expr: ExprLike) -> Expr:
        return Expr.join("(", json_expr, " + 0.0)")


@dataclass(frozen=True)
class _Float32Adapter(_AbstractFloatAdapter):
    """Type adapter implementation for float32."""


@dataclass(frozen=True)
class _Float64Adapter(_AbstractFloatAdapter):
    """Type adapter implementation for float32."""


FLOAT32_ADAPTER: Final[TypeAdapter] = _Float32Adapter()
FLOAT64_ADAPTER: Final[TypeAdapter] = _Float64Adapter()


class _TimestampAdapter(AbstractPrimitiveAdapter):
    def default_expr(self) -> Expr:
        return Expr.local("_EPOCH", Timestamp.EPOCH)

    def to_frozen_expr(self, arg_expr: ExprLike) -> Expr:
        timestamp_local = Expr.local("Timestamp", Timestamp)
        return Expr.join(
            "(",
            arg_expr,
            " if ",
            arg_expr,
            ".__class__ is ",
            timestamp_local,
            " else ",
            timestamp_local,
            "(unix_millis=",
            arg_expr,
            ".unix_millis))",
        )

    def is_not_default_expr(self, arg_expr: ExprLike, attr_expr: ExprLike) -> Expr:
        return Expr.join(arg_expr, ".unix_millis")

    def to_json_expr(self, in_expr: ExprLike, readable: bool) -> Expr:
        if readable:
            return Expr.join(in_expr, "._trj()")
        else:
            return Expr.join(in_expr, ".unix_millis")

    def from_json_expr(self, json_expr: ExprLike) -> Expr:
        fn = Expr.local("_timestamp_from_json", _timestamp_from_json)
        return Expr.join(fn, "(", json_expr, ")")


def _timestamp_from_json(json: Any) -> Timestamp:
    if json.__class__ is int or isinstance(json, int):
        return Timestamp(unix_millis=json)
    else:
        return Timestamp(unix_millis=json["unix_millis"])


TIMESTAMP_ADAPTER: Final[TypeAdapter] = _TimestampAdapter()


class _StringAdapter(AbstractPrimitiveAdapter):
    def default_expr(self) -> ExprLike:
        return '""'

    def to_frozen_expr(self, arg_expr: ExprLike) -> Expr:
        return Expr.join("('' + ", arg_expr, ")")

    def is_not_default_expr(self, arg_expr: ExprLike, attr_expr: ExprLike) -> ExprLike:
        return arg_expr

    def to_json_expr(self, in_expr: ExprLike, readable: bool) -> ExprLike:
        return in_expr

    def from_json_expr(self, json_expr: ExprLike) -> Expr:
        return Expr.join("('' + (", json_expr, " or ''))")


STRING_ADAPTER: Final[TypeAdapter] = _StringAdapter()


class _BytesAdapter(AbstractPrimitiveAdapter):
    _fromhex_fn: Final = bytes.fromhex

    def default_expr(self) -> ExprLike:
        return 'b""'

    def to_frozen_expr(self, arg_expr: ExprLike) -> Expr:
        return Expr.join("(b'' + ", arg_expr, ")")

    def is_not_default_expr(self, arg_expr: ExprLike, attr_expr: ExprLike) -> ExprLike:
        return arg_expr

    def to_json_expr(
        self,
        in_expr: ExprLike,
        readable: bool,
    ) -> Expr:
        return Expr.join(in_expr, ".hex()")

    def from_json_expr(self, json_expr: ExprLike) -> Expr:
        return Expr.join(
            Expr.local("fromhex", _BytesAdapter._fromhex_fn), "(", json_expr, ")"
        )


BYTES_ADAPTER: Final[TypeAdapter] = _BytesAdapter()
