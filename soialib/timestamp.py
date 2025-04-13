import dataclasses
import datetime
from typing import Any, Final, Union, cast, final, overload


@final
class Timestamp:
    __slots__ = ("unix_millis",)

    unix_millis: int

    def __init__(self, unix_millis: int, _formatted: str = ""):
        object.__setattr__(
            self,
            "unix_millis",
            round(min(max(unix_millis, -8640000000000000), 8640000000000000)),
        )

    @staticmethod
    def from_unix_millis(unix_millis: int) -> "Timestamp":
        return Timestamp(unix_millis=unix_millis)

    @staticmethod
    def from_unix_seconds(unix_seconds: float) -> "Timestamp":
        return Timestamp(unix_millis=round(unix_seconds * 1000))

    @staticmethod
    def from_datetime(dt: datetime.datetime) -> "Timestamp":
        return Timestamp.from_unix_seconds(dt.timestamp())

    @staticmethod
    def now() -> "Timestamp":
        return Timestamp.from_datetime(datetime.datetime.now(tz=datetime.timezone.utc))

    EPOCH: Final["Timestamp"] = cast("Timestamp", ...)
    MIN: Final["Timestamp"] = cast("Timestamp", ...)
    MAX: Final["Timestamp"] = cast("Timestamp", ...)

    @property
    def unix_seconds(self) -> float:
        return self.unix_millis / 1000.0

    def to_datetime_or_raise(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            self.unix_seconds, tz=datetime.timezone.utc
        )

    def __add__(self, td: datetime.timedelta) -> "Timestamp":
        return Timestamp(
            unix_millis=self.unix_millis + round(td.total_seconds() * 1000)
        )

    @overload
    def __sub__(self, other: datetime.timedelta) -> "Timestamp": ...
    @overload
    def __sub__(self, other: "Timestamp") -> datetime.timedelta: ...

    def __sub__(
        self, other: Union["Timestamp", datetime.timedelta]
    ) -> Union["Timestamp", datetime.timedelta]:
        if isinstance(other, Timestamp):
            return datetime.timedelta(milliseconds=self.unix_millis - other.unix_millis)
        else:
            return self.__add__(-other)

    def __lt__(self, other: "Timestamp"):
        return self.unix_millis < other.unix_millis

    def __gt__(self, other: "Timestamp"):
        return self.unix_millis > other.unix_millis

    def __le__(self, other: "Timestamp"):
        return self.unix_millis <= other.unix_millis

    def __ge__(self, other: "Timestamp"):
        return self.unix_millis >= other.unix_millis

    def __eq__(self, other: Any):
        if isinstance(other, Timestamp):
            return other.unix_millis == self.unix_millis
        return NotImplemented

    def __hash__(self):
        return hash(("ts", self.unix_millis))

    def __repr__(self) -> str:
        iso = self._iso_format()
        if iso:
            return f"Timestamp(\n  unix_millis={self.unix_millis},\n  _formatted='{iso}',\n)"
        else:
            return f"Timestamp(unix_millis={self.unix_millis})"

    def __setattr__(self, name: str, value: Any):
        raise dataclasses.FrozenInstanceError(self.__class__.__qualname__)

    def __delattr__(self, name: str):
        raise dataclasses.FrozenInstanceError(self.__class__.__qualname__)

    def _trj(self) -> Any:
        """To readable JSON."""
        iso = self._iso_format()
        if iso:
            return {
                "unix_millis": self.unix_millis,
                "formatted": iso,
            }
        else:
            return {
                "unix_millis": self.unix_millis,
            }

    def _iso_format(self) -> str:
        try:
            dt = self.to_datetime_or_raise()
        except Exception:
            return ""
        if dt:
            ret = dt.isoformat()
            bad_suffix = "+00:00"
            if ret.endswith(bad_suffix):
                ret = ret[0 : -len(bad_suffix)] + "Z"
        return ret


# Use 'setattr' because we marked these class attributes as Final.
setattr(Timestamp, "EPOCH", Timestamp.from_unix_millis(0))
setattr(Timestamp, "MIN", Timestamp.from_unix_millis(-8640000000000000))
setattr(Timestamp, "MAX", Timestamp.from_unix_millis(8640000000000000))
