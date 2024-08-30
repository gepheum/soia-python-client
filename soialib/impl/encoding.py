from struct import pack
from typing import Final

from soialib.impl.function_maker import Expr

EMPTY_STRING_WIRE: Final[Expr] = Expr.local("EMPTY_STRING_WIRE", bytes([242]))
STRING_WIRE: Final[Expr] = Expr.local("STRING_WIRE", bytes([243]))
EMPTY_BYTE_STRING_WIRE: Final[Expr] = Expr.local("EMPTY_BYTE_STRING_WIRE", bytes([244]))
BYTE_STRING_WIRE: Final[Expr] = Expr.local("BYTE_STRING_WIRE", bytes([245]))
SMALL_ARRAY_WIRES: Final[Expr] = Expr.local(
    "SMALL_ARRAY_WIRES", tuple(bytes(b) for b in range(246, 250))
)
ARRAY_WIRE: Final[Expr] = Expr.local("ARRAY_WIRE", bytes(250))
NULL_WIRE: Final[Expr] = Expr.local("NULL_WIRE", bytes([255]))

_LOW_INT_BYTES: Final[tuple[bytes, ...]] = tuple([bytes([i]) for i in range(232)])
_ZERO_BYTES: Final[bytes] = _LOW_INT_BYTES[0]
_ONE_BYTES: Final[bytes] = _LOW_INT_BYTES[1]

LOW_INT_BYTES: Final[Expr] = Expr.local("LOW_INT_BYTES", _LOW_INT_BYTES)
ZERO_BYTES: Final[Expr] = Expr.local("ZERO_BYTES_LOCAL", _ZERO_BYTES)
ONE_BYTES: Final[Expr] = Expr.local("ONE_BYTES_LOCAL", _ONE_BYTES)

PACK: Final[Expr] = Expr.local("pack", pack)


def _len_bytes_high(l: int) -> bytes:
    if l < 65536:
        return pack("H", l)
    elif l < 2147483648:
        return pack("I", l)
    raise OverflowError(f"len={l}")


LEN_BYTES: Final[Expr] = Expr.join(
    "(",
    LOW_INT_BYTES,
    "[l] if l < 232 else ",
    Expr.local("len_bytes_high", _len_bytes_high),
    "(l))",
)
