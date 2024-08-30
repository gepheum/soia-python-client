# TODO: test
# TODO: unrecognized fields (and handles removed fields)

from collections.abc import Callable, Sequence
from dataclasses import FrozenInstanceError, dataclass
from typing import Any, Final, Union

from soialib import spec as _spec
from soialib.impl import primitives
from soialib.impl.function_maker import (
    BodyBuilder,
    BodySpan,
    Expr,
    ExprLike,
    Line,
    make_function,
)
from soialib.impl.repr import repr_impl
from soialib.impl.type_adapter import TypeAdapter


class EnumAdapter(TypeAdapter):
    __slots__ = (
        "spec",
        "gen_class",
        "private_is_enum_attr",
        "finalization_state",
    )

    spec: Final[_spec.Enum]
    gen_class: Final[type]  # AKA the base class
    private_is_enum_attr: Final[str]
    # 0: has not started; 1: in progress; 2: done
    finalization_state: int

    def __init__(self, spec: _spec.Enum):
        self.finalization_state = 0
        self.spec = spec
        base_class = self.gen_class = _make_base_class(spec)

        private_is_enum_attr = _name_private_is_enum_attr(spec.id)
        self.private_is_enum_attr = private_is_enum_attr
        # TODO: comment
        setattr(base_class, private_is_enum_attr, True)

        # Add the constants.
        for constant_field in self.all_constant_fields:
            constant_class = _make_constant_class(base_class, constant_field)
            constant = constant_class()
            setattr(base_class, constant_field.attribute, constant)

    def finalize(
        self,
        resolve_type_fn: Callable[[_spec.Type], TypeAdapter],
    ) -> None:
        if self.finalization_state != 0:
            # Finalization is either in progress or done.
            return
        # Mark finalization as in progress.
        self.finalization_state = 1

        base_class = self.gen_class

        # Resolve the type of every value field.
        value_fields = [
            _make_value_field(f, resolve_type_fn(f.type), base_class)
            for f in self.spec.value_fields
        ]

        # Aim to have dependencies finalized *before* the dependent. It's not always
        # possible, because there can be cyclic dependencies.
        # The function returned by the do_x_fn() method of a dependency is marginally
        # faster if the dependency is finalized. If the dependency is not finalized,
        # this function is a "forwarding" function.
        for value_field in value_fields:
            value_field.field_type.finalize(resolve_type_fn)

        # Add the wrap static factory methods.
        for value_field in value_fields:
            wrap_fn = _make_wrap_fn(value_field)
            setattr(base_class, f"wrap_{value_field.spec.name}", wrap_fn)

        base_class._fj = _make_from_json_fn(
            self.all_constant_fields, value_fields, base_class
        )

        # Mark finalization as done.
        self.finalization_state = 2

    @property
    def all_constant_fields(self) -> list[_spec.ConstantField]:
        unknown_field = _spec.ConstantField(
            name="?",
            number=0,
            _attribute="UNKNOWN",
        )
        return list(self.spec.constant_fields) + [unknown_field]

    def default_expr(self) -> Expr:
        return Expr.local("_d?", self.gen_class.UNKNOWN)

    def to_frozen_expr(self, arg_expr: ExprLike) -> Expr:
        return Expr.join(
            "(",
            arg_expr,
            f".{self.private_is_enum_attr} and ",
            arg_expr,
            ")",
        )

    def is_not_default_expr(self, arg_expr: ExprLike, attr_expr: ExprLike) -> Expr:
        return Expr.join(arg_expr, "._number")

    def to_json_expr(self, in_expr: ExprLike, readable: bool) -> Expr:
        return Expr.join(in_expr, "._rj" if readable else "._dj")

    def from_json_expr(self, json_expr: ExprLike) -> Expr:
        fn_name = "_fj"
        # TODO: comment
        from_json_fn = getattr(self.gen_class, fn_name, None)
        if from_json_fn:
            return Expr.join(Expr.local("_fj?", from_json_fn), "(", json_expr, ")")
        else:
            return Expr.join(
                Expr.local("_cls?", self.gen_class), f".{fn_name}(", json_expr, ")"
            )


def _make_base_class(spec: _spec.Enum) -> type:
    record_hash = hash(spec.id)

    class BaseClass:
        __slots__ = ("value",)

        kind: str
        value: Any

        def __init__(self, never: Any):
            raise TypeError("Cannot call the constructor of a soia enum")

        @property
        def union(self) -> Any:
            return self

        def __setattr__(self, name: str, value: Any):
            raise FrozenInstanceError(self.__class__.__qualname__)

        def __delattr__(self, name: str):
            raise FrozenInstanceError(self.__class__.__qualname__)

        def __eq__(self, other: Any) -> bool:
            # TODO: make it work with unrecognized versus UNKNOWN
            if isinstance(other, BaseClass):
                return other.kind == self.kind and other.value == self.value
            return NotImplemented

        def __hash__(self) -> int:
            return hash((record_hash, self.kind, self.value))

    BaseClass.__name__ = spec.class_name
    BaseClass.__qualname__ = spec.class_qualname

    return BaseClass


def _make_constant_class(base_class: type, spec: _spec.ConstantField) -> type:
    class ConstantClass(base_class):
        __slots__ = ()

        kind: Final[str] = spec.name
        _number: Final[int] = spec.number
        # dense JSON
        _dj: Final[int] = spec.number
        # readable JSON
        _rj: Final[str] = spec.name
        # has value
        _hv: Final[bool] = False

        def __init__(self):
            # Do not call super().__init__().
            object.__setattr__(self, "value", None)

        def __repr__(self) -> str:
            return f"{base_class.__qualname__}.{spec.attribute}"

    return ConstantClass


def _make_value_class(
    base_class: type,
    field_spec: _spec.ValueField,
    field_type: TypeAdapter,
) -> type:
    number = field_spec.number

    class ValueClass(base_class):
        __slots__ = ()

        kind: Final[str] = field_spec.name
        _number: Final[int] = number
        # has value
        _hv: Final[bool] = True

        def __init__(self):
            # Do not call super().__init__().
            pass

        def __repr__(self) -> str:
            value_repr = repr_impl(self.value)
            if value_repr.complex:
                body = f"\n  {value_repr.indented}\n"
            else:
                body = value_repr.repr
            return f"{base_class.__qualname__}.wrap_{field_spec.name}({body})"

    ret = ValueClass

    ret._dj = property(
        make_function(
            name="to_dense_json",
            params=["self"],
            body=[
                Line.join(
                    f"return [{field_spec.number}, ",
                    field_type.to_json_expr("self.value", readable=False),
                    "]",
                ),
            ],
        )
    )

    ret._rj = property(
        make_function(
            name="to_readable_json",
            params=["self"],
            body=[
                Line.join(
                    "return {",
                    f'"kind": "{field_spec.name}", "value": ',
                    field_type.to_json_expr("self.value", readable=True),
                    "}",
                ),
            ],
        )
    )

    return ret


@dataclass(frozen=True)
class _ValueField:
    spec: _spec.ValueField
    field_type: TypeAdapter
    value_class: type


def _make_value_field(
    spec: _spec.ValueField, field_type: TypeAdapter, base_class: type
) -> _ValueField:
    return _ValueField(
        spec=spec,
        field_type=field_type,
        value_class=_make_value_class(
            base_class=base_class, field_spec=spec, field_type=field_type
        ),
    )


def _make_wrap_fn(field: _ValueField) -> Callable[[Any], Any]:
    builder = BodyBuilder()
    builder.append_ln("ret = ", Expr.local("value_class", field.value_class), "()")
    builder.append_ln(
        Expr.local("setattr", object.__setattr__),
        "(ret, 'value', ",
        field.field_type.to_frozen_expr(Expr.join("value")),
        ")",
    )
    builder.append_ln("return ret")
    return make_function(
        name="wrap",
        params=["value"],
        body=builder.build(),
    )


def _make_from_json_fn(
    constant_fields: Sequence[_spec.ConstantField],
    value_fields: Sequence[_ValueField],
    base_class: type,
) -> Callable[[Any], Any]:
    obj_setattr_local = Expr.local("obj_settatr", object.__setattr__)

    key_to_constant: dict[Union[int, str], Any] = {}
    for field in constant_fields:
        constant = getattr(base_class, field.attribute)
        key_to_constant[field.number] = constant
        key_to_constant[field.name] = constant
    key_to_constant_local = Expr.local("key_to_constant", key_to_constant)
    unknown_constant = key_to_constant[0]
    unknown_constant_local = Expr.local("unknown_constant", unknown_constant)

    numbers: list[int] = []
    names: list[str] = []
    key_to_field: dict[Union[int, str], _ValueField] = {}
    for field in value_fields:
        numbers.append(field.spec.number)
        names.append(field.spec.name)
        key_to_field[field.spec.number] = field
        key_to_field[field.spec.name] = field
    value_keys_local = Expr.local("value_keys", set(key_to_field.keys()))

    builder = BodyBuilder()
    # The reason why we wrap the function inside a 'while' is explained below.
    builder.append_ln("while True:")

    # DENSE FORMAT
    if len(constant_fields) == 1:
        builder.append_ln("  if json == 0:")
        builder.append_ln("    return ", unknown_constant_local)
    else:
        builder.append_ln("  if json.__class__ is int:")
        builder.append_ln("    try:")
        builder.append_ln("      return ", key_to_constant_local, "[json]")
        builder.append_ln("    except:")
        # TODO: handle unrecognized fields!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        builder.append_ln("      return ...")

    def append_number_branches(numbers: list[int], indent: str) -> None:
        if len(numbers) == 1:
            number = numbers[0]
            field = key_to_field[number]
            value_class_local = Expr.local("cls?", field.value_class)
            value_expr = field.field_type.from_json_expr(Expr.join("json[1]"))
            builder.append_ln(f"{indent}ret = ", value_class_local, "()")
            builder.append_ln(indent, obj_setattr_local, "(ret, ", value_expr, ")")
            builder.append_ln(f"{indent}return ret")
        else:
            indented = f"  {indent}"
            mid_index = int(len(numbers) / 2)
            mid_number = numbers[mid_index - 1]
            operator = "==" if mid_index == 1 else "<="
            builder.append_ln(f"{indent}if number {operator} {mid_number}:")
            append_number_branches(numbers[0:mid_index], indented)
            builder.append_ln(f"{indent}else:")
            append_number_branches(numbers[mid_index:], indented)

    builder.append_ln("  elif json.__class__ is list:")
    if not value_fields:
        # TODO: handle unrecognized fields!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        builder.append_ln("    return ...")
    else:
        if len(value_fields) == 1:
            builder.append_ln(f"    if number != {value_fields[0].spec.number}:")
        else:
            builder.append_ln("    if number not in ", value_keys_local, ":")
        # TODO: handle unrecognized fields!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        builder.append_ln("      return ...")
        builder.append_ln("    number = json[0]")
        append_number_branches(sorted(numbers), "    ")

    # READABLE FORMAT
    if len(constant_fields) == 1:
        builder.append_ln("  elif json == '?':")
        builder.append_ln("    return ", unknown_constant_local)
    else:
        builder.append_ln("  if isinstance(json, str):")
        builder.append_ln("    try:")
        builder.append_ln("      return ", key_to_constant_local, "[json]")
        builder.append_ln("    except:")
        # TODO: comment
        builder.append_ln("      return ", unknown_constant_local)

    def append_name_branches(names: list[str], indent: str) -> None:
        if len(names) == 1:
            name = names[0]
            field = key_to_field[name]
            value_class_local = Expr.local("cls?", field.value_class)
            value_expr = field.field_type.from_json_expr("json['value']")
            builder.append_ln(f"{indent}ret = ", value_class_local, "()")
            builder.append_ln(indent, obj_setattr_local, "(ret, ", value_expr, ")")
            builder.append_ln(f"{indent}return ret")
        else:
            indented = f"  {indent}"
            mid_index = int(len(names) / 2)
            mid_name = names[mid_index - 1]
            operator = "==" if mid_index == 1 else "<="
            builder.append_ln(f"{indent}if name {operator} '{mid_name}':")
            append_name_branches(names[0:mid_index], indented)
            builder.append_ln(f"{indent}else:")
            append_name_branches(names[mid_index:], indented)

    builder.append_ln("  elif isinstance(json, dict):")
    if not value_fields:
        # TODO: comment
        builder.append_ln("    return ", unknown_constant_local)
    else:
        builder.append_ln("    name = json['name']")
        builder.append_ln("    if name not in ", value_keys_local, ":")
        # TODO: comment
        builder.append_ln("      return ", unknown_constant_local)
        builder.append_ln("    else:")
        append_name_branches(sorted(names), "      ")

    return make_function(
        name="from_json",
        params=["json"],
        body=builder.build(),
    )


def _name_private_is_enum_attr(record_id: str) -> str:
    record_name = _spec.RecordId.parse(record_id).name
    hex_hash = hex(abs(hash(record_id)))[:6]
    return f"_is_{record_name}_{hex_hash}"
