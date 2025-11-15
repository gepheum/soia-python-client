import copy
from collections.abc import Callable, Sequence
from dataclasses import FrozenInstanceError, dataclass
from typing import Any, Final, Generic, Union

from soia import _spec, reflection
from soia._impl.binary import decode_int64, decode_unused, encode_int64
from soia._impl.function_maker import BodyBuilder, Expr, ExprLike, Line, make_function
from soia._impl.repr import repr_impl
from soia._impl.type_adapter import ByteStream, T, TypeAdapter


class EnumAdapter(Generic[T], TypeAdapter[T]):
    __slots__ = (
        "spec",
        "gen_class",
        "private_is_enum_attr",
        "finalization_state",
        "wrapper_fields",
    )

    spec: Final[_spec.Enum]
    gen_class: Final[type]  # AKA the base class
    private_is_enum_attr: Final[str]
    # 0: has not started; 1: in progress; 2: done
    finalization_state: int
    wrapper_fields: tuple["_WrapperField", ...]

    def __init__(self, spec: _spec.Enum):
        self.finalization_state = 0
        self.spec = spec
        base_class = self.gen_class = _make_base_class(spec)

        def forward_decode(stream: ByteStream) -> T:
            return base_class._decode(stream)

        # Will be overridden at finalization time.
        base_class._decode = forward_decode

        private_is_enum_attr = _name_private_is_enum_attr(spec.id)
        self.private_is_enum_attr = private_is_enum_attr
        setattr(base_class, private_is_enum_attr, True)

        # Add the constants.
        for constant_field in self.all_constant_fields:
            constant_class = _make_constant_class(base_class, constant_field)
            constant = constant_class()
            setattr(base_class, constant_field.attribute, constant)

        # Add the Kind type alias.
        setattr(base_class, "Kind", str)

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

        # Resolve the type of every wrapper field.
        self.wrapper_fields = wrapper_fields = tuple(
            _make_wrapper_field(f, resolve_type_fn(f.type), base_class)
            for f in self.spec.wrapper_fields
        )

        # Aim to have dependencies finalized *before* the dependent. It's not always
        # possible, because there can be cyclic dependencies.
        # The function returned by the do_x_fn() method of a dependency is marginally
        # faster if the dependency is finalized. If the dependency is not finalized,
        # this function is a "forwarding" function.
        for wrapper_field in wrapper_fields:
            wrapper_field.field_type.finalize(resolve_type_fn)

        # Add the wrap static factory methods.
        for wrapper_field in wrapper_fields:
            wrap_fn = _make_wrap_fn(wrapper_field)
            setattr(base_class, f"wrap_{wrapper_field.spec.name}", wrap_fn)
            # Check if the field type is a struct type.
            field_type = resolve_type_fn(wrapper_field.spec.type)
            frozen_class = field_type.frozen_class_of_struct()
            if frozen_class:
                create_fn = _make_create_fn(wrap_fn, frozen_class)
                setattr(base_class, f"create_{wrapper_field.spec.name}", create_fn)

        unrecognized_class = _make_unrecognized_class(base_class)

        base_class._fj = _make_from_json_fn(
            self.all_constant_fields,
            wrapper_fields,
            set(self.spec.removed_numbers),
            base_class=base_class,
            unrecognized_class=unrecognized_class,
        )
        base_class._decode = _make_decode_fn(
            self.all_constant_fields,
            wrapper_fields,
            set(self.spec.removed_numbers),
            base_class=base_class,
            unrecognized_class=unrecognized_class,
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

    def from_json_expr(
        self, json_expr: ExprLike, keep_unrecognized_expr: ExprLike
    ) -> Expr:
        fn_name = "_fj"
        from_json_fn = getattr(self.gen_class, fn_name, None)
        if from_json_fn:
            return Expr.join(
                Expr.local("_fj?", from_json_fn),
                "(",
                json_expr,
                ", ",
                keep_unrecognized_expr,
                ")",
            )
        else:
            return Expr.join(
                Expr.local("_cls?", self.gen_class),
                f".{fn_name}(",
                json_expr,
                ", ",
                keep_unrecognized_expr,
                ")",
            )

    def encode_fn(self) -> Callable[[T, bytearray], None]:
        return _encode_impl

    def decode_fn(self) -> Callable[[ByteStream], T]:
        return self.gen_class._decode

    def get_type(self) -> reflection.Type:
        return reflection.RecordType(
            kind="record",
            value=self.spec.id,
        )

    def register_records(
        self,
        registry: dict[str, reflection.Record],
    ) -> None:
        record_id = self.spec.id
        if record_id in registry:
            return
        registry[record_id] = reflection.Record(
            kind="enum",
            id=record_id,
            fields=tuple(
                reflection.Field(
                    name=field.name,
                    number=field.number,
                    type=None,
                )
                for field in self.all_constant_fields
                if field.number != 0
            )
            + tuple(
                reflection.Field(
                    name=field.spec.name,
                    number=field.spec.number,
                    type=field.field_type.get_type(),
                )
                for field in self.wrapper_fields
            ),
            removed_numbers=self.spec.removed_numbers,
        )
        for field in self.wrapper_fields:
            field.field_type.register_records(registry)

    def frozen_class_of_struct(self) -> type | None:
        return None


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

        def __bool__(self) -> bool:
            return self.kind != "?"

        def __setattr__(self, name: str, value: Any):
            raise FrozenInstanceError(self.__class__.__qualname__)

        def __delattr__(self, name: str):
            raise FrozenInstanceError(self.__class__.__qualname__)

        def __eq__(self, other: Any) -> bool:
            if isinstance(other, BaseClass):
                return other.kind == self.kind and other.value == self.value
            return NotImplemented

        def __hash__(self) -> int:
            return hash((record_hash, self.kind, self.value))

    BaseClass.__name__ = spec.class_name
    BaseClass.__qualname__ = spec.class_qualname

    return BaseClass


def _make_constant_class(base_class: type, spec: _spec.ConstantField) -> type:
    byte_array = bytearray()
    encode_int64(spec.number, byte_array)

    class Constant(base_class):
        __slots__ = ()

        kind: Final[str] = spec.name
        _number: Final[int] = spec.number
        # dense JSON
        _dj: Final[int] = spec.number
        # readable JSON
        _rj: Final[str] = spec.name
        # has value
        _hv: Final[bool] = False
        _bytes: Final[bytes | None] = bytes(byte_array)

        def __init__(self):
            # Do not call super().__init__().
            object.__setattr__(self, "value", None)

        def __repr__(self) -> str:
            return f"{base_class.__qualname__}.{spec.attribute}"

    return Constant


def _make_unrecognized_class(base_class: type) -> type:
    """Wraps around an unrecognized dense JSON.

    Looks and acts just like the UNKNOWN constant, except that its JSON representation
    is the original unrecognized dense JSON.
    """

    class Unrecognized(base_class):
        __slots__ = ("_dj", "_bytes")

        kind: Final[str] = "?"
        _number: Final[int] = 0
        # dense JSON
        _dj: list[Any] | int
        _bytes: bytes
        # readable JSON
        _rj: Final[str] = "?"
        # has value
        _hv: Final[bool] = False

        def __init__(self, dj: list[Any] | int, bytes: bytes):
            # Do not call super().__init__().
            object.__setattr__(self, "_dj", copy.deepcopy(dj))
            object.__setattr__(self, "_bytes", bytes)
            object.__setattr__(self, "value", None)

        def __repr__(self) -> str:
            return f"{base_class.__qualname__}.UNKNOWN"

    return Unrecognized


def _make_value_class(
    base_class: type,
    field_spec: _spec.WrapperField,
    field_type: TypeAdapter,
) -> type:
    number = field_spec.number

    class Value(base_class):
        __slots__ = ()

        kind: Final[str] = field_spec.name
        _number: Final[int] = number
        # has value
        _hv: Final[bool] = True
        _bytes: Final[None] = None

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

    ret = Value

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

    bytes_prefix = bytearray()
    if number in range(1, 5):
        bytes_prefix.append(250 + number)
    else:
        bytes_prefix.append(248)
        encode_int64(number, bytes_prefix)

    ret._enc = make_function(
        name="encode",
        params=["self", "buffer"],
        body=[
            f"buffer.extend({bytes_prefix})",
            Line.join(
                Expr.local("encode_value", field_type.encode_fn()),
                "(self.value, buffer)",
            ),
        ],
    )

    return ret


def _encode_impl(
    value: Any,
    buffer: bytearray,
) -> None:
    if value._bytes:
        buffer.extend(value._bytes)
    else:
        value._enc(buffer)


@dataclass(frozen=True)
class _WrapperField:
    spec: _spec.WrapperField
    field_type: TypeAdapter
    value_class: type


def _make_wrapper_field(
    spec: _spec.WrapperField, field_type: TypeAdapter, base_class: type
) -> _WrapperField:
    return _WrapperField(
        spec=spec,
        field_type=field_type,
        value_class=_make_value_class(
            base_class=base_class, field_spec=spec, field_type=field_type
        ),
    )


def _make_wrap_fn(field: _WrapperField) -> Callable[[Any], Any]:
    builder = BodyBuilder()
    builder.append_ln("ret = ", Expr.local("value_class", field.value_class), "()")
    builder.append_ln(
        Expr.local("setattr", object.__setattr__),
        "(ret, 'value', ",
        field.field_type.to_frozen_expr("value"),
        ")",
    )
    builder.append_ln("return ret")
    return make_function(
        name="wrap",
        params=["value"],
        body=builder.build(),
    )


def _make_create_fn(wrap_fn: Callable[[Any], Any], frozen_class: type) -> Callable:
    def create(**kwargs):
        return wrap_fn(frozen_class(**kwargs))

    return create


def _make_from_json_fn(
    constant_fields: Sequence[_spec.ConstantField],
    wrapper_fields: Sequence[_WrapperField],
    removed_numbers: set[int],
    base_class: type,
    unrecognized_class: type,
) -> Callable[[Any], Any]:
    unrecognized_class_local = Expr.local("Unrecognized", unrecognized_class)
    obj_setattr_local = Expr.local("obj_settatr", object.__setattr__)
    removed_numbers_tuple = tuple(sorted(removed_numbers))

    key_to_constant: dict[Union[int, str], Any] = {}
    for field in constant_fields:
        constant = getattr(base_class, field.attribute)
        key_to_constant[field.number] = constant
        key_to_constant[field.name] = constant
    key_to_constant_local = Expr.local("key_to_constant", key_to_constant)
    unknown_constant = key_to_constant[0]
    unknown_constant_local = Expr.local("unknown_constant", unknown_constant)

    number_to_wrapper_field: dict[int, _WrapperField] = {}
    name_to_wrapper_field: dict[str, _WrapperField] = {}
    for field in wrapper_fields:
        number_to_wrapper_field[field.spec.number] = field
        name_to_wrapper_field[field.spec.name] = field
    wrapper_field_numbers = tuple(sorted(number_to_wrapper_field.keys()))
    wrapper_field_names = tuple(sorted(name_to_wrapper_field.keys()))

    builder = BodyBuilder()
    # The reason why we wrap the function inside a 'while' is explained below.
    builder.append_ln("while True:")

    # DENSE FORMAT
    if len(constant_fields) == 1:
        builder.append_ln("  if json == 0:")
        builder.append_ln("    return ", unknown_constant_local)
    else:
        # `json.__class__ is int` is significantly faster than `isinstance(json, int)`
        builder.append_ln("  if json.__class__ is int:")
        builder.append_ln("    try:")
        builder.append_ln("      return ", key_to_constant_local, "[json]")
        builder.append_ln("    except:")
        if removed_numbers:
            builder.append_ln(
                f"      if json in {removed_numbers_tuple} or not keep_unrecognized_fields:"
            )
            builder.append_ln("        return ", unknown_constant_local)
        builder.append_ln("      return ", unrecognized_class_local, "(json, b'\\0')")

    def append_number_branches(numbers: Sequence[int], indent: str) -> None:
        if len(numbers) == 1:
            number = numbers[0]
            field = number_to_wrapper_field[number]
            value_class_local = Expr.local("cls?", field.value_class)
            value_expr = field.field_type.from_json_expr(
                "json[1]", "keep_unrecognized_fields"
            )
            builder.append_ln(f"{indent}ret = ", value_class_local, "()")
            builder.append_ln(
                indent, obj_setattr_local, '(ret, "value", ', value_expr, ")"
            )
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

    # `json.__class__ is list` is significantly faster than `isinstance(json, list)`
    builder.append_ln("  elif json.__class__ is list:")
    builder.append_ln("    number = json[0]")
    if not wrapper_fields:
        # The field was either removed or is an unrecognized field.
        if removed_numbers:
            builder.append_ln(
                f"    if number in {removed_numbers_tuple} or not keep_unrecognized_fields:"
            )
            builder.append_ln("      return ", unknown_constant_local)
        builder.append_ln("    return ", unrecognized_class_local, "(json, b'\\0')")
    else:
        builder.append_ln(f"    if number not in {wrapper_field_numbers}:")
        if removed_numbers:
            builder.append_ln(
                f"      if number in {removed_numbers_tuple} or not keep_unrecognized_fields:"
            )
            builder.append_ln("        return ", unknown_constant_local)
        builder.append_ln("      return ", unrecognized_class_local, "(json, b'\\0')")
        append_number_branches(wrapper_field_numbers, "    ")

    # READABLE FORMAT
    if len(constant_fields) == 1:
        builder.append_ln("  elif json == '?':")
        builder.append_ln("    return ", unknown_constant_local)
    else:
        builder.append_ln("  if isinstance(json, str):")
        builder.append_ln("    try:")
        builder.append_ln("      return ", key_to_constant_local, "[json]")
        builder.append_ln("    except:")
        # In readable mode, drop unrecognized values and use UNKNOWN instead.
        builder.append_ln("      return ", unknown_constant_local)

    def append_name_branches(names: Sequence[str], indent: str) -> None:
        if len(names) == 1:
            name = names[0]
            field = name_to_wrapper_field[name]
            value_class_local = Expr.local("cls?", field.value_class)
            value_expr = field.field_type.from_json_expr(
                "json['value']", "keep_unrecognized_fields"
            )
            builder.append_ln(f"{indent}ret = ", value_class_local, "()")
            builder.append_ln(
                indent, obj_setattr_local, '(ret, "value", ', value_expr, ")"
            )
            builder.append_ln(f"{indent}return ret")
        else:
            indented = f"  {indent}"
            mid_index = int(len(names) / 2)
            mid_name = names[mid_index - 1]
            operator = "==" if mid_index == 1 else "<="
            builder.append_ln(f"{indent}if kind {operator} '{mid_name}':")
            append_name_branches(names[0:mid_index], indented)
            builder.append_ln(f"{indent}else:")
            append_name_branches(names[mid_index:], indented)

    builder.append_ln("  elif isinstance(json, dict):")
    if not wrapper_fields:
        builder.append_ln("    return ", unknown_constant_local)
    else:
        builder.append_ln("    kind = json['kind']")
        builder.append_ln(f"    if kind not in {wrapper_field_names}:")
        builder.append_ln("      return ", unknown_constant_local)
        builder.append_ln("    else:")
        append_name_branches(wrapper_field_names, "      ")

    # In the unlikely event that json.loads() returns an instance of a subclass of int.
    builder.append_ln("  elif isinstance(json, int):")
    builder.append_ln("    json = int(json)")
    builder.append_ln("  elif isinstance(json, list):")
    builder.append_ln("    json = list(json)")
    builder.append_ln("  else:")
    builder.append_ln("    return TypeError()")

    return make_function(
        name="from_json",
        params=["json", "keep_unrecognized_fields"],
        body=builder.build(),
    )


def _make_decode_fn(
    constant_fields: Sequence[_spec.ConstantField],
    wrapper_fields: Sequence[_WrapperField],
    removed_numbers: set[int],
    base_class: type,
    unrecognized_class: type,
) -> Callable[[ByteStream], Any]:
    unrecognized_class_local = Expr.local("Unrecognized", unrecognized_class)
    obj_setattr_local = Expr.local("obj_settatr", object.__setattr__)

    number_to_constant: dict[int, Any] = {}
    for field in constant_fields:
        constant = getattr(base_class, field.attribute)
        number_to_constant[field.number] = constant
    number_to_constant_local = Expr.local("number_to_constant", number_to_constant)
    removed_numbers_tuple = tuple(sorted(removed_numbers))
    unknown_constant = number_to_constant[0]
    unknown_constant_local = Expr.local("unknown_constant", unknown_constant)

    number_to_wrapper_field: dict[int, _WrapperField] = {}
    for field in wrapper_fields:
        number_to_wrapper_field[field.spec.number] = field
    wrapper_field_numbers = tuple(sorted(number_to_wrapper_field.keys()))

    builder = BodyBuilder()
    builder.append_ln("start_offset = stream.position")
    builder.append_ln("wire = stream.buffer[start_offset]")
    builder.append_ln("if wire <= 238:")
    # A number
    builder.append_ln("  if wire < 232:")
    builder.append_ln("    stream.position += 1")
    builder.append_ln("    number = wire")
    builder.append_ln("  else:")
    builder.append_ln(
        "    number = ", Expr.local("decode_int64", decode_int64), "(stream)"
    )
    builder.append_ln("  try:")
    builder.append_ln("    return ", number_to_constant_local, "[number]")
    builder.append_ln("  except:")
    if removed_numbers:
        builder.append_ln(
            f"    if number in {removed_numbers_tuple} or not stream.keep_unrecognized_fields:"
        )
        builder.append_ln("      return ", unknown_constant_local)
    builder.append_ln("    bytes = stream.buffer[start_offset:stream.position]")
    builder.append_ln("    return ", unrecognized_class_local, "(0, bytes)")
    # An array of 2
    builder.append_ln("stream.position += 1")
    builder.append_ln("if wire == 248:")
    builder.append_ln(
        "  number = ", Expr.local("decode_int64", decode_int64), "(stream)"
    )
    builder.append_ln("else:")
    builder.append_ln("  number = wire - 250")

    def append_number_branches(numbers: Sequence[int], indent: str) -> None:
        if len(numbers) == 1:
            number = numbers[0]
            field = number_to_wrapper_field[number]
            value_class_local = Expr.local("cls?", field.value_class)
            decode_local = Expr.local("decode?", field.field_type.decode_fn())
            value_expr = Expr.join(decode_local, "(stream)")
            builder.append_ln(f"{indent}ret = ", value_class_local, "()")
            builder.append_ln(
                indent, obj_setattr_local, '(ret, "value", ', value_expr, ")"
            )
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

    if not wrapper_fields:
        # The field was either removed or is an unrecognized field.
        builder.append_ln(Expr.local("decode_unused", decode_unused), "(stream)")
        if removed_numbers:
            builder.append_ln(
                f"if number in {removed_numbers_tuple} or not stream.keep_unrecognized_fields:"
            )
            builder.append_ln("  return ", unknown_constant_local)
        builder.append_ln("bytes = stream.buffer[start_offset:stream.position]")
        builder.append_ln("return ", unrecognized_class_local, "(0, bytes)")
    else:
        builder.append_ln(f"if number not in {wrapper_field_numbers}:")
        builder.append_ln("  ", Expr.local("decode_unused", decode_unused), "(stream)")
        if removed_numbers:
            builder.append_ln(
                f"  if number in {removed_numbers_tuple} or not stream.keep_unrecognized_fields:"
            )
            builder.append_ln("    return ", unknown_constant_local)
        builder.append_ln("  bytes = stream.buffer[start_offset:stream.position]")
        builder.append_ln("  return ", unrecognized_class_local, "(0, bytes)")
        append_number_branches(wrapper_field_numbers, "")

    return make_function(
        name="decode",
        params=["stream"],
        body=builder.build(),
    )


def _name_private_is_enum_attr(record_id: str) -> str:
    record_name = _spec.RecordId.parse(record_id).name
    hex_hash = hex(abs(hash(record_id)))[:6]
    return f"_is_{record_name}_{hex_hash}"
