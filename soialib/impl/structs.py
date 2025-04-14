import copy
from collections.abc import Callable, Sequence
from dataclasses import FrozenInstanceError, dataclass
from typing import Any, Final, Union, cast

from soialib import spec as _spec
from soialib.impl.function_maker import (
    BodyBuilder,
    Expr,
    ExprLike,
    Line,
    LineSpan,
    LineSpanLike,
    Param,
    Params,
    make_function,
)
from soialib.impl.repr import repr_impl
from soialib.impl.type_adapter import TypeAdapter


class StructAdapter(TypeAdapter):
    __slots__ = (
        "spec",
        "record_hash",
        "gen_class",
        "mutable_class",
        "simple_class",
        "private_is_frozen_attr",
        "finalization_state",
    )

    spec: Final[_spec.Struct]
    record_hash: Final[int]
    # The frozen class.
    gen_class: Final[type]
    mutable_class: Final[type]
    simple_class: Final[type]
    private_is_frozen_attr: Final[str]

    # 0: has not started; 1: in progress; 2: done
    finalization_state: int

    def __init__(self, spec: _spec.Struct):
        self.finalization_state = 0
        self.spec = spec
        self.record_hash = hash(spec.id)

        self.private_is_frozen_attr = _name_private_is_frozen_attr(spec.id)

        slots = tuple(f.attribute for f in self.spec.fields) + (
            # Unrecognized fields encountered during deserialization.
            "_unrecognized",
            # Lowest number greater than the number of every field with a non-default
            # value.
            "_array_len",
        )
        frozen_class = self.gen_class = _make_dataclass(slots)
        frozen_class.__name__ = spec.class_name
        frozen_class.__qualname__ = spec.class_qualname
        frozen_class.__setattr__ = cast(Any, _Frozen.__setattr__)
        frozen_class.__delattr__ = cast(Any, _Frozen.__delattr__)
        # We haven't added an __init__ method to the frozen class yet, so frozen_class()
        # returns an object with no attribute set. We'll set the attributes of DEFAULT
        # at the finalization step.
        frozen_class.DEFAULT = frozen_class()

        mutable_class = self.mutable_class = _make_dataclass(slots)
        mutable_class.__name__ = "Mutable"
        mutable_class.__qualname__ = f"{spec.class_qualname}.Mutable"
        frozen_class.Mutable = mutable_class
        frozen_class.OrMutable = Union[frozen_class, mutable_class]

        # The 'simple' class is a class which only has __slots__ defined.
        # To construct instances of the frozen class from internal implementation,
        # instead of calling the constructor of the frozen class, we use the following
        # technique: create an instance of the simple class, assign all the attributes,
        # then assign the frozen class to the __class__ attribute.
        # Reason why it's faster: we don't need to call object.__setattr__().
        self.simple_class = _make_dataclass(slots)

    def finalize(
        self,
        resolve_type_fn: Callable[[_spec.Type], TypeAdapter],
    ) -> None:
        if self.finalization_state != 0:
            # Finalization is either in progress or done.
            return
        # Mark finalization as in progress.
        self.finalization_state = 1

        # Resolve the type of every field.
        fields = tuple(
            sorted(
                (_Field(f, resolve_type_fn(f.type)) for f in self.spec.fields),
                key=lambda f: f.field.number,
            )
        )

        # Aim to have dependencies finalized *before* the dependent. It's not always
        # possible, because there can be cyclic dependencies.
        # The function returned by the do_x_fn() method of a dependency is marginally
        # faster if the dependency is finalized. If the dependency is not finalized,
        # this function is a "forwarding" function.
        for field in fields:
            field.type.finalize(resolve_type_fn)

        frozen_class = self.gen_class
        mutable_class = self.mutable_class
        simple_class = self.simple_class

        frozen_class.to_frozen = _identity
        frozen_class.to_mutable = _make_to_mutable_fn(
            mutable_class=mutable_class,
            simple_class=simple_class,
            fields=fields,
        )
        mutable_class.to_frozen = _make_to_frozen_fn(
            frozen_class=frozen_class,
            simple_class=simple_class,
            fields=fields,
        )
        setattr(frozen_class, self.private_is_frozen_attr, True)
        setattr(mutable_class, self.private_is_frozen_attr, False)

        frozen_class.__init__ = cast(
            Any,
            _make_frozen_class_init_fn(
                fields,
                frozen_class=frozen_class,
                simple_class=simple_class,
            ),
        )
        mutable_class.__init__ = cast(Any, _make_mutable_class_init_fn(fields))

        frozen_class.__eq__ = _make_eq_fn(fields)
        frozen_class.__hash__ = cast(Any, _make_hash_fn(fields, self.record_hash))
        frozen_class.__repr__ = mutable_class.__repr__ = cast(
            Any, _make_repr_fn(fields)
        )

        frozen_class._tdj = _make_to_dense_json_fn(fields=fields)
        frozen_class._trj = _make_to_readable_json_fn(fields=fields)
        frozen_class._fj = _make_from_json_fn(
            frozen_class=frozen_class,
            simple_class=simple_class,
            fields=fields,
            removed_numbers=self.spec.removed_numbers,
        )

        # Initialize DEFAULT.
        _init_default(self.gen_class.DEFAULT, fields)

        # Define mutable getters
        for field in fields:
            if field.field.has_mutable_getter:
                mutable_getter = _make_mutable_getter(field)
                mutable_getter_name = mutable_getter.__name__
                setattr(mutable_class, mutable_getter_name, property(mutable_getter))

        # Mark finalization as done.
        self.finalization_state = 2

    def default_expr(self) -> Expr:
        return Expr.local("_d?", self.gen_class.DEFAULT)

    def to_frozen_expr(self, arg_expr: ExprLike) -> Expr:
        # The goal of referring to private_is_frozen_attr is to raise an error if the
        # struct has the wrong type.
        return Expr.join(
            "(",
            arg_expr,
            " if ",
            arg_expr,
            f".{self.private_is_frozen_attr} else ",
            arg_expr,
            ".to_frozen())",
        )

    def is_not_default_expr(self, arg_expr: ExprLike, attr_expr: ExprLike) -> Expr:
        return Expr.join(attr_expr, "._array_len")

    def to_json_expr(
        self,
        in_expr: ExprLike,
        readable: bool,
    ) -> Expr:
        return Expr.join(in_expr, "._trj" if readable else "._tdj", "()")

    def from_json_expr(self, json_expr: ExprLike) -> Expr:
        fn_name = "_fj"
        # The _fj method may not have been added to the class yet.
        from_json_fn = getattr(self.gen_class, fn_name, None)
        if from_json_fn:
            return Expr.join(Expr.local("_fj?", from_json_fn), "(", json_expr, ")")
        else:
            return Expr.join(
                Expr.local("_cls?", self.gen_class), f".{fn_name}(", json_expr, ")"
            )


class _Frozen:
    def __setattr__(self, name: str, value: Any):
        raise FrozenInstanceError(self.__class__.__qualname__)

    def __delattr__(self, name: str):
        raise FrozenInstanceError(self.__class__.__qualname__)


def _make_dataclass(slots: tuple[str, ...]) -> type:
    class Result:
        __slots__ = slots

    return Result


def _identity(input: Any) -> Any:
    return input


@dataclass(frozen=True)
class _Field:
    field: _spec.Field
    type: TypeAdapter


def _make_frozen_class_init_fn(
    fields: Sequence[_Field],
    frozen_class: type,
    simple_class: type,
) -> Callable[[Any], None]:
    """
    Returns the implementation of the __init__() method of the frozen class.
    """

    # Set the params.
    params: Params = ["_self"]
    if fields:
        params.append("*")
    for field in fields:
        params.append(
            Param(
                name=field.field.attribute,
                default=field.type.default_expr(),
            )
        )

    builder = BodyBuilder()
    # Since __setattr__() was overridden to raise errors in order to make the class
    # immutable, the only way to set attributes in the constructor is to call
    # object.__setattr__().
    obj_setattr = Expr.local("_setattr", object.__setattr__)

    def array_len_expr() -> Expr:
        spans: list[LineSpanLike] = []
        # Fields are sorted by number.
        for field in reversed(fields):
            spans.append(
                LineSpan.join(
                    f"{field.field.number + 1} if ",
                    field.type.is_not_default_expr(
                        arg_expr=field.field.attribute,
                        attr_expr=f"_self.{field.field.attribute}",
                    ),
                    " else ",
                )
            )
        spans.append("0")
        return Expr.join(*spans)

    if len(fields) < 3:
        # If the class has less than 3 fields, it is faster to assign every field with
        # object.__setattr__().
        for field in fields:
            attribute = field.field.attribute
            builder.append_ln(
                obj_setattr,
                '(_self, "',
                attribute,
                '", ',
                field.type.to_frozen_expr(attribute),
                ")",
            )
        # Set the _unrecognized field.
        builder.append_ln(obj_setattr, '(_self, "_unrecognized", ())')
        # Set array length.
        builder.append_ln(
            obj_setattr,
            '(_self, "_array_len", ',
            array_len_expr(),
            ")",
        )
    else:
        # If the class has 4 fields or more, it is faster to first change the __class__
        # attribute of the object so it's no longer immutable, assign all the attributes
        # with regular assignment, and then change back the __class__ attribute.
        builder.append_ln(
            obj_setattr,
            '(_self, "__class__", ',
            Expr.local("Simple", simple_class),
            ")",
        )
        for field in fields:
            attribute = field.field.attribute
            builder.append_ln(
                "_self.",
                attribute,
                " = ",
                field.type.to_frozen_expr(attribute),
            )
        # Set the _unrecognized field.
        builder.append_ln("_self._unrecognized = ()")
        # Set array length.
        builder.append_ln("_self._array_len = ", array_len_expr())
        # Change back the __class__.
        builder.append_ln("_self.__class__ = ", Expr.local("Frozen", frozen_class))

    return make_function(
        name="__init__",
        params=params,
        body=builder.build(),
    )


def _make_mutable_class_init_fn(fields: Sequence[_Field]) -> Callable[[Any], None]:
    """
    Returns the implementation of the __init__() method of the mutable class.
    """

    params: Params = ["_self"]
    builder = BodyBuilder()
    for field in fields:
        attribute = field.field.attribute
        params.append(
            Param(
                name=attribute,
                default=field.type.default_expr(),
            )
        )
        builder.append_ln(
            "_self.",
            attribute,
            " = ",
            attribute,
        )
    builder.append_ln("_self._unrecognized = ()")
    return make_function(
        name="__init__",
        params=params,
        body=builder.build(),
    )


def _make_to_mutable_fn(
    mutable_class: type,
    simple_class: type,
    fields: Sequence[_Field],
) -> Callable[[Any], Any]:
    """
    Returns the implementation of the to_mutable() method of the frozen class.
    """
    builder = BodyBuilder()
    # Create an instance of the simple class. We'll later change its __class__ attr.
    builder.append_ln(
        "ret = ",
        Expr.local("Simple", simple_class),
        "()",
    )
    for field in fields:
        attribute = field.field.attribute
        builder.append_ln("ret.", attribute, " = self.", attribute)
    builder.append_ln("ret._unrecognized = self._unrecognized")
    builder.append_ln(
        "ret.__class__ = ",
        Expr.local("mutable_class", mutable_class),
    )
    builder.append_ln("return ret")
    return make_function(
        name="to_mutable",
        params=["self"],
        body=builder.build(),
    )


def _make_to_frozen_fn(
    frozen_class: type,
    simple_class: type,
    fields: Sequence[_Field],
) -> Callable[[Any], Any]:
    """
    Returns the implementation of the to_frozen() method of the mutable class.
    """

    builder = BodyBuilder()
    # Create an instance of the simple class. We'll later change its __class__ attr.
    builder.append_ln(
        "ret = ",
        Expr.local("Simple", simple_class),
        "()",
    )
    for field in fields:
        attribute = field.field.attribute
        builder.append_ln(
            "ret.",
            attribute,
            " = ",
            field.type.to_frozen_expr(f"self.{attribute}"),
        )

    # Set the _unrecognized field.
    builder.append_ln("ret._unrecognized = self._unrecognized")

    def array_len_expr() -> Expr:
        spans: list[LineSpanLike] = []
        spans.append(
            LineSpan.join(
                f"{_get_num_slots(fields)} + ",
                Expr.local("_len", len),
                "(ret._unrecognized) if ret._unrecognized else ",
            )
        )
        # Fields are sorted by number.
        for field in reversed(fields):
            attr_expr = f"ret.{field.field.attribute}"
            spans.append(
                LineSpan.join(
                    f"{field.field.number + 1} if ",
                    field.type.is_not_default_expr(attr_expr, attr_expr),
                    " else ",
                )
            )
        spans.append("0")
        return Expr.join(*spans)

    # Set the _unrecognized field.
    builder.append_ln("ret._unrecognized = self._unrecognized")
    # Set array length.
    builder.append_ln("ret._array_len = ", array_len_expr())

    builder.append_ln(
        "ret.__class__ = ",
        Expr.local("Frozen", frozen_class),
    )
    builder.append_ln("return ret")
    return make_function(
        name="to_frozen",
        params=["self"],
        body=builder.build(),
    )


def _make_eq_fn(
    fields: Sequence[_Field],
) -> Callable[[Any], Any]:
    """
    Returns the implementation of the __eq__() method of the frozen class.
    """

    builder = BodyBuilder()
    builder.append_ln("if other is self:")
    builder.append_ln("  return True")
    builder.append_ln("if other.__class__ is self.__class__:")
    operands: list[ExprLike]
    if fields:
        attr: Callable[[_Field], str] = lambda f: f.field.attribute
        operands = [Expr.join(f"self.{attr(f)} == other.{attr(f)}") for f in fields]
    else:
        operands = ["True"]
    builder.append_ln("  return ", Expr.join(*operands, separator=" and "))
    builder.append_ln("return ", Expr.local("NotImplemented", NotImplemented))
    return make_function(
        name="__eq__",
        params=["self", "other"],
        body=builder.build(),
    )


def _make_hash_fn(
    fields: Sequence[_Field],
    record_hash: int,
) -> Callable[[Any], Any]:
    """
    Returns the implementation of the __hash__() method of the frozen class.
    """

    components: list[ExprLike] = []
    components.append(str(record_hash))
    for field in fields:
        components.append(f"self.{field.field.attribute}")
    return make_function(
        name="__hash__",
        params=["self"],
        body=[Line.join("return hash((", Expr.join(*components, separator=", "), "))")],
    )


def _make_repr_fn(fields: Sequence[_Field]) -> Callable[[Any], Any]:
    """
    Returns the implementation of the __repr__() method of both the frozen class and the
    mutable class.
    """

    builder = BodyBuilder()
    builder.append_ln("if self is getattr(self.__class__, 'DEFAULT', None):")
    builder.append_ln("  return f'{self.__class__.__qualname__}.DEFAULT'")
    builder.append_ln("assignments = []")
    builder.append_ln("any_complex = False")
    builder.append_ln("is_mutable = self.__class__.__name__ == 'Mutable'")
    repr_local = Expr.local("repr", repr_impl)
    for field in fields:
        attribute = field.field.attribute
        # is_not_default_expr only works on a frozen expression.
        to_frozen_expr = field.type.to_frozen_expr(f"(self.{attribute})")
        is_not_default_expr = field.type.is_not_default_expr(
            to_frozen_expr, to_frozen_expr
        )
        builder.append_ln("if is_mutable or ", is_not_default_expr, ":")
        builder.append_ln("  r = ", repr_local, f"(self.{attribute})")
        builder.append_ln(f"  assignments.append(f'{attribute}={{r.indented}}')")
        builder.append_ln("  any_complex = any_complex or r.complex")
    builder.append_ln("if len(assignments) <= 1 and not any_complex:")
    builder.append_ln("  body = ''.join(assignments)")
    builder.append_ln("else:")
    builder.append_ln("  body = '\\n' + ''.join(f'  {a},\\n' for a in assignments)")
    builder.append_ln("return f'{self.__class__.__qualname__}({body})'")

    return make_function(
        name="__repr__",
        params=["self"],
        body=builder.build(),
    )


def _make_to_dense_json_fn(fields: Sequence[_Field]) -> Callable[[Any], Any]:
    builder = BodyBuilder()
    builder.append_ln("l = self._array_len")
    builder.append_ln("ret = [0] * l")
    for field in fields:
        builder.append_ln(f"if l <= {field.field.number}:")
        builder.append_ln("  return ret")
        builder.append_ln(
            f"ret[{field.field.number}] = ",
            field.type.to_json_expr(
                f"self.{field.field.attribute}",
                readable=False,
            ),
        )
    num_slots = _get_num_slots(fields)
    builder.append_ln(f"if l <= {num_slots}:")
    builder.append_ln("  return ret")
    builder.append_ln(f"ret[{num_slots}:] = self._unrecognized")
    builder.append_ln("return ret")
    return make_function(
        name="to_dense_json",
        params=["self"],
        body=builder.build(),
    )


def _make_to_readable_json_fn(fields: Sequence[_Field]) -> Callable[[Any], Any]:
    builder = BodyBuilder()
    builder.append_ln("ret = {}")
    for field in fields:
        attr_expr = f"self.{field.field.attribute}"
        builder.append_ln(
            "if ",
            field.type.is_not_default_expr(attr_expr, attr_expr),
            ":",
        )
        builder.append_ln(
            f'  ret["{field.field.name}"] = ',
            field.type.to_json_expr(
                attr_expr,
                readable=True,
            ),
        )
    builder.append_ln("return ret")
    return make_function(
        name="to_readable_json",
        params=["self"],
        body=builder.build(),
    )


def _make_from_json_fn(
    frozen_class: type,
    simple_class: type,
    fields: Sequence[_Field],
    removed_numbers: tuple[int, ...],
) -> Callable[[Any], Any]:
    builder = BodyBuilder()
    builder.append_ln("if not json:")
    builder.append_ln("  return ", Expr.local("DEFAULT", frozen_class.DEFAULT))
    builder.append_ln("ret = ", Expr.local("Simple", simple_class), "()")
    builder.append_ln(
        "if ",
        Expr.local("isinstance", isinstance),
        "(json, ",
        Expr.local("list", list),
        "):",
    )
    # JSON array (dense flavor)
    builder.append_ln(
        "  array_len = ",
        Expr.local("len", len),
        "(json)",
    )
    for field in fields:
        name = field.field.name
        number = field.field.number
        item_expr = f"json[{number}]"
        builder.append_ln(
            f"  ret.{field.field.attribute} = ",
            field.type.default_expr(),
            f" if array_len <= {number} else ",
            field.type.from_json_expr(item_expr),
        )
    num_slots = _get_num_slots(fields)
    builder.append_ln(f"  if array_len <= {num_slots}:")
    builder.append_ln("    ret._unrecognized = ()")
    builder.append_ln(
        "    ret._array_len = ",
        _adjust_array_len_expr("array_len", removed_numbers),
    )
    builder.append_ln("  else:")
    builder.append_ln(
        "    ret._unrecognized = ",
        Expr.local("deepcopy", copy.deepcopy),
        f"(json[{num_slots}:])",
    )
    builder.append_ln("    ret._array_len = array_len")

    builder.append_ln("else:")
    builder.append_ln("  array_len = 0")
    # JSON object (readable flavor)
    for field in fields:
        name = field.field.name
        lvalue = f"ret.{field.field.attribute}"
        builder.append_ln(f'  if "{name}" in json:')
        builder.append_ln(f"    array_len = {field.field.number}")
        builder.append_ln(
            f"    {lvalue} = ",
            field.type.from_json_expr(f'json["{name}"]'),
        )
        builder.append_ln("  else:")
        builder.append_ln(f"    {lvalue} = ", field.type.default_expr())
    # Drop unrecognized fields in readable mode.
    builder.append_ln("  ret._unrecognized = ()")
    builder.append_ln("  ret._array_len = array_len")

    builder.append_ln("ret.__class__ = ", Expr.local("Frozen", frozen_class))
    builder.append_ln("return ret")

    return make_function(
        name="from_json",
        params=["json"],
        body=builder.build(),
    )


def _adjust_array_len_expr(var: str, removed_numbers: tuple[int, ...]) -> str:
    """
    When parsing a dense JSON or decoding a binary string, we can reuse the array length
    in the decoded struct, but we need to account for possibly newly-removed fields. The
    last field of the adjusted array length cannot be a removed field.

    Let's imagine that field number 3 was removed from a struct.
    This function would return the following expression:
        array_len if array_len <= 3 else 3 if array_len == 4 else array_len
    """

    @dataclass
    class _RemovedSpan:
        """Sequence of consecutive removed fields."""

        # Number of the first removed field.
        begin: int = 0
        # Number after the last removed field.
        end: int = 0

    def get_removed_spans() -> list[_RemovedSpan]:
        ret: list[_RemovedSpan] = []
        for number in sorted(removed_numbers):
            last = ret[-1] if ret else None
            if last and last.end == number:
                last.end = number + 1
            else:
                ret.append(_RemovedSpan(number, number + 1))
        return ret

    removed_spans = get_removed_spans()

    ret = ""
    lower_bound = 0
    for s in removed_spans:
        if s.begin == lower_bound:
            ret += f"{s.begin} if {var} <= {s.end} else "
        elif s.end == s.begin + 1:
            # Similar to the expression in 'else' but uses '==' instead of '<='
            ret += (
                f"{var} if {var} <= {s.begin} else {s.begin} if {var} == {s.end} else "
            )
        else:
            ret += (
                f"{var} if {var} <= {s.begin} else {s.begin} if {var} <= {s.end} else "
            )
        lower_bound = s.end + 1
    ret += var
    return ret


def _init_default(default: Any, fields: Sequence[_Field]) -> None:
    for field in fields:
        attribute = field.field.attribute
        get_field_default = make_function(
            name="get_default",
            params=(),
            body=(Line.join("return ", field.type.default_expr()),),
        )
        object.__setattr__(default, attribute, get_field_default())
    object.__setattr__(default, "_unrecognized", ())
    object.__setattr__(default, "_array_len", 0)


def _make_mutable_getter(field: _Field) -> Callable[[Any], Any]:
    # Two cases: the field either has struct type or array type.
    attribute = field.field.attribute
    builder = BodyBuilder()
    if isinstance(field.type, StructAdapter):
        frozen_class = field.type.gen_class
        mutable_class = frozen_class.Mutable
        builder.append_ln(
            f"if self.{attribute}.__class__ is ",
            Expr.local("mutable_class", mutable_class),
            ":",
        )
        builder.append_ln(f"  return self.{attribute}")
        builder.append_ln(
            f"if self.{attribute}.__class__ is ",
            Expr.local("frozen_class", frozen_class),
            ":",
        )
        builder.append_ln(f"  self.{attribute} = self.{attribute}.to_mutable()")
        builder.append_ln(f"  return self.{attribute}")
        expected = f"{frozen_class.__qualname__} or {mutable_class.__qualname__}"
        found = f"self.{attribute}.__class__.__name__"
        builder.append_ln(
            "raise ",
            Expr.local("TypeError", TypeError),
            f"(f'expected: {expected}; found: {{{found}}}')",
        )
    else:
        builder.append_ln(f"if not isinstance(self.{attribute}, list):")
        builder.append_ln(f"  self.{attribute} = list(self.{attribute})")
        builder.append_ln(f"return self.{attribute}")
    return make_function(
        name=f"mutable_{field.field.name}",
        params=["self"],
        body=builder.build(),
    )


def _name_private_is_frozen_attr(record_id: str) -> str:
    record_name = _spec.RecordId.parse(record_id).name
    hex_hash = hex(abs(hash(record_id)))[:6]
    return f"_is_{record_name}_{hex_hash}"


def _get_num_slots(fields: Sequence[_Field]) -> int:
    return (fields[-1].field.number + 1) if fields else 0
