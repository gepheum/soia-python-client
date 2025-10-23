import base64
import struct
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final, final

from soia import _spec, reflection
from soia._impl.binary import (
    decode_int64,
    encode_int32,
    encode_length_prefix,
    make_decode_number_fn,
)
from soia._impl.function_maker import Expr, ExprLike
from soia._impl.timestamp import Timestamp
from soia._impl.type_adapter import ByteStream, TypeAdapter, T


class AbstractPrimitiveAdapter(TypeAdapter[T]):
    @final
    def finalize(
        self,
        resolve_type_fn: Callable[[_spec.Type], "TypeAdapter"],
    ) -> None:
        pass

    @final
    def register_records(
        self,
        registry: dict[str, reflection.Record],
    ) -> None:
        pass

    @final
    def frozen_class_of_struct(self) -> type | None:
        return None


class _BoolAdapter(AbstractPrimitiveAdapter[bool]):
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
            return Expr.join("(True if ", in_expr, " else False)")
        else:
            return Expr.join("(1 if ", in_expr, " else 0)")

    def from_json_expr(self, json_expr: ExprLike) -> Expr:
        return Expr.join("(True if ", json_expr, " else False)")

    def encode(
        self,
        value: bool,
        buffer: bytearray,
    ) -> None:
        buffer.append(1 if value else 0)

    def decode(
        self,
        stream: ByteStream,
    ) -> bool: ...

    def get_type(self) -> reflection.Type:
        return reflection.PrimitiveType(
            kind="primitive",
            value="bool",
        )


_BoolAdapter.decode = make_decode_number_fn("bool", is_method=True)


BOOL_ADAPTER: Final[TypeAdapter[bool]] = _BoolAdapter()


@dataclass(frozen=True)
class _AbstractIntAdapter(AbstractPrimitiveAdapter[int]):
    """Type adapter implementation for int32, int64 and uint64."""

    def default_expr(self) -> ExprLike:
        return "0"

    def to_frozen_expr(self, arg_expr: ExprLike) -> Expr:
        # Must accept float inputs and turn them into ints.
        return Expr.join("(0).__class__(", arg_expr, ")")

    def is_not_default_expr(self, arg_expr: ExprLike, attr_expr: ExprLike) -> ExprLike:
        return arg_expr

    def from_json_expr(self, json_expr: ExprLike) -> Expr:
        # Must accept float inputs and string inputs and turn them into ints.
        return Expr.join(
            "(0).__class__(",
            json_expr,
            ")",
        )


@dataclass(frozen=True)
class _Int32Adapter(_AbstractIntAdapter):
    def to_json_expr(self, in_expr: ExprLike, readable: bool) -> Expr:
        return Expr.join(
            "(-2147483648 if ",
            in_expr,
            " <= -2147483648 else ",
            in_expr,
            " if ",
            in_expr,
            " < 2147483647 else 2147483647)",
        )

    def encode(
        self,
        value: int,
        buffer: bytearray,
    ) -> None:
        encode_int32(value, buffer)

    def decode(
        self,
        stream: ByteStream,
    ) -> int: ...

    def get_type(self) -> reflection.Type:
        return reflection.PrimitiveType(
            kind="primitive",
            value="int32",
        )


_Int32Adapter.decode = make_decode_number_fn("int32", is_method=True)


def _int64_to_json(i: int) -> int | str:
    if i < -9007199254740991:  # min safe integer in JavaScript
        if i <= -9223372036854775808:
            return "-9223372036854775808"
        else:
            return str(i)
    elif i <= 9007199254740991:  # max safe integer in JavaScript
        return i
    elif i < 9223372036854775807:
        return str(i)
    else:
        return "9223372036854775807"


@dataclass(frozen=True)
class _Int64Adapter(_AbstractIntAdapter):
    def to_json_expr(self, in_expr: ExprLike, readable: bool) -> Expr:
        return Expr.join(Expr.local("int64_to_json", _int64_to_json), "(", in_expr, ")")

    def encode(
        self,
        value: int,
        buffer: bytearray,
    ) -> None:
        if -2147483648 <= value <= 2147483647:
            encode_int32(value, buffer)
        else:
            buffer.append(238)
            buffer.extend(struct.pack("<q", value))

    def decode(
        self,
        stream: ByteStream,
    ) -> int: ...

    def get_type(self) -> reflection.Type:
        return reflection.PrimitiveType(
            kind="primitive",
            value="int64",
        )


_Int64Adapter.decode = make_decode_number_fn("int64", is_method=True)


def _uint64_to_json(i: int) -> int | str:
    if i <= 0:
        return 0
    elif i <= 9007199254740991:  # max safe integer in JavaScript
        return i
    elif i < 18446744073709551615:
        return f"{i}"
    else:
        return "18446744073709551615"


@dataclass(frozen=True)
class _Uint64Adapter(_AbstractIntAdapter):
    def to_json_expr(self, in_expr: ExprLike, readable: bool) -> Expr:
        return Expr.join(
            Expr.local("uint64_to_json", _uint64_to_json), "(", in_expr, ")"
        )

    def encode(
        self,
        value: int,
        buffer: bytearray,
    ) -> None:
        if value < 232:
            buffer.append(value)
        elif value < 65536:
            buffer.append(232)
            buffer.extend(struct.pack("<H", value))
        elif value < 4294967296:
            buffer.append(233)
            buffer.extend(struct.pack("<I", value))
        else:
            buffer.append(234)
            buffer.extend(struct.pack("<Q", value))

    def decode(
        self,
        stream: ByteStream,
    ) -> int: ...

    def get_type(self) -> reflection.Type:
        return reflection.PrimitiveType(
            kind="primitive",
            value="uint64",
        )


_Uint64Adapter.decode = make_decode_number_fn("uint64", is_method=True)


INT32_ADAPTER: Final[TypeAdapter[int]] = _Int32Adapter()
INT64_ADAPTER: Final[TypeAdapter[int]] = _Int64Adapter()
UINT64_ADAPTER: Final[TypeAdapter[int]] = _Uint64Adapter()


@dataclass(frozen=True)
class _AbstractFloatAdapter(AbstractPrimitiveAdapter[float]):
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

    def decode(
        self,
        stream: ByteStream,
    ) -> float: ...


_AbstractFloatAdapter.decode = make_decode_number_fn("float", is_method=True)


@dataclass(frozen=True)
class _Float32Adapter(_AbstractFloatAdapter):
    """Type adapter implementation for float32."""

    def encode(
        self,
        value: float,
        buffer: bytearray,
    ) -> None:
        if value == 0.0:
            buffer.append(0)
        else:
            buffer.append(240)
            buffer.extend(struct.pack("<f", value))

    def get_type(self) -> reflection.Type:
        return reflection.PrimitiveType(
            kind="primitive",
            value="float32",
        )


@dataclass(frozen=True)
class _Float64Adapter(_AbstractFloatAdapter):
    """Type adapter implementation for float64."""

    def encode(
        self,
        value: float,
        buffer: bytearray,
    ) -> None:
        if value == 0.0:
            buffer.append(0)
        else:
            buffer.append(241)
            buffer.extend(struct.pack("<d", value))

    def get_type(self) -> reflection.Type:
        return reflection.PrimitiveType(
            kind="primitive",
            value="float64",
        )


FLOAT32_ADAPTER: Final[TypeAdapter[float]] = _Float32Adapter()
FLOAT64_ADAPTER: Final[TypeAdapter[float]] = _Float64Adapter()


def _clamp_unix_millis(unix_millis: int) -> int:
    """Clamp unix milliseconds to valid range for JavaScript dates."""
    return max(-8640000000000000, min(unix_millis, 8640000000000000))


class _TimestampAdapter(AbstractPrimitiveAdapter[Timestamp]):
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

    def encode(
        self,
        value: Timestamp,
        buffer: bytearray,
    ) -> None:
        unix_millis = _clamp_unix_millis(value.unix_millis)
        if unix_millis == 0:
            buffer.append(0)
        else:
            buffer.append(239)
            buffer.extend(struct.pack("<q", unix_millis))

    def decode(
        self,
        stream: ByteStream,
    ) -> Timestamp:
        return Timestamp(unix_millis=_clamp_unix_millis(decode_int64(stream)))

    def get_type(self) -> reflection.Type:
        return reflection.PrimitiveType(
            kind="primitive",
            value="timestamp",
        )


def _timestamp_from_json(json: Any) -> Timestamp:
    if json.__class__ is int or isinstance(json, int):
        return Timestamp(unix_millis=json)
    else:
        return Timestamp(unix_millis=json["unix_millis"])


TIMESTAMP_ADAPTER: Final[TypeAdapter[Timestamp]] = _TimestampAdapter()


class _StringAdapter(AbstractPrimitiveAdapter[str]):
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

    def encode(
        self,
        value: str,
        buffer: bytearray,
    ) -> None:
        if not value:
            buffer.append(242)
        else:
            buffer.append(243)
            bytes_data = value.encode("utf-8")
            length = len(bytes_data)
            encode_length_prefix(length, buffer)
            buffer.extend(bytes_data)

    def decode(
        self,
        stream: ByteStream,
    ) -> str:
        wire = stream.read(1)[0]
        if wire == 242:
            return ""
        else:
            # Should be wire 243
            length = decode_int64(stream)
            bytes_data = stream.read(length)
            return bytes_data.decode("utf-8")

    def get_type(self) -> reflection.Type:
        return reflection.PrimitiveType(
            kind="primitive",
            value="string",
        )


STRING_ADAPTER: Final[TypeAdapter] = _StringAdapter()


class _BytesAdapter(AbstractPrimitiveAdapter[bytes]):
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
        return Expr.join(
            Expr.local("b64encode", base64.b64encode),
            "(",
            in_expr,
            ").decode('utf-8')",
        )

    def from_json_expr(self, json_expr: ExprLike) -> Expr:
        return Expr.join(
            Expr.local("b64decode", base64.b64decode), "(", json_expr, ' or "")'
        )

    def encode(
        self,
        value: bytes,
        buffer: bytearray,
    ) -> None:
        if len(value) == 0:
            buffer.append(244)
        else:
            buffer.append(245)
            length = len(value)
            encode_length_prefix(length, buffer)
            buffer.extend(value)

    def decode(
        self,
        stream: ByteStream,
    ) -> bytes:
        wire = stream.read_wire()
        if wire in (0, 244):
            return b""
        else:
            # Should be wire 245
            length = decode_int64(stream)
            return stream.read(length)

    def get_type(self) -> reflection.Type:
        return reflection.PrimitiveType(
            kind="primitive",
            value="bytes",
        )


BYTES_ADAPTER: Final[TypeAdapter[bytes]] = _BytesAdapter()
